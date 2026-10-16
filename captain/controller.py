import concurrent.futures
import threading
import time
from .actions import Actions
from .jobs import JobManager, TERMINAL
from .memory import Memory
from .model import Ollama


class Controller:
    def __init__(self, config, root, emit=print, silence=lambda: None, model=None):
        self.config, self.root = config, root
        self.emit, self.silence = emit, silence
        self.jobs = JobManager(root / "jobs", config.max_jobs)
        self.memory = Memory(root / "memory.sqlite3")
        self.actions = Actions(config, self.jobs, self.memory)
        self.model = model or Ollama(config)
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.generation = 0
        self.private, self.focus = False, False
        self.lock = threading.RLock()
        self.pending = None
        self.awaiting_stop = False
        self.history = []  # bounded RAM-only conversation; never persisted
        self.reported = {j["id"] for j in self.jobs.snapshot()}
        self.closed = threading.Event()
        threading.Thread(target=self._monitor, daemon=True).start()

    def _monitor(self):
        while not self.closed.wait(.25):
            for job in self.jobs.snapshot():
                if job["status"] in TERMINAL and job["id"] not in self.reported:
                    self.reported.add(job["id"])
                    self.emit(f"{job['label']}: {job['status']}. Output saved locally. "
                              "A completed process does not establish a vulnerability.")

    def submit(self, text, allow_actions=True):
        text = text.strip()
        normalized = text.lower().strip(" .!?")
        for prefix in ("hey captain, ", "hey captain ", "captain, ", "captain "):
            if normalized.startswith(prefix):
                text = text[len(prefix):]
                normalized = text.lower().strip(" .!?")
                break
        with self.lock:
            if normalized == "stop":
                self.generation += 1  # stale model responses may finish but cannot execute
                self.awaiting_stop = True
                self.silence()
                self.emit("What do you want me to stop, Boss?")
                return
            if normalized in {"quiet", "be quiet"}:
                self.silence()
                return
            if normalized in {"stop everything", "cancel everything"}:
                self.generation += 1
                self.awaiting_stop = False
                self.silence()
                self.jobs.cancel_all()
                self.emit("Stopping all managed jobs. I'll verify their outcomes.")
                return
            if normalized in {"resume", "never mind", "nevermind"}:
                self.awaiting_stop = False
                self.emit("Ready for your next instruction.")
                return
            if normalized.startswith(("stop ", "cancel ")) or self.awaiting_stop:
                needle = normalized.removeprefix("stop ").removeprefix("cancel ").removeprefix("the ")
                matches = [j for j in self.jobs.snapshot() if j["status"] not in TERMINAL and
                           (needle in j["label"].lower() or needle == j["id"])]
                if len(matches) == 1:
                    self.jobs.cancel(matches[0]["id"])
                    self.awaiting_stop = False
                    self.emit("Stopping " + matches[0]["label"] + ".")
                else:
                    self.emit("Please specify a running job name or ID.")
                return
            if normalized in {"status", "progress", "how's it going", "what are you doing"}:
                jobs = self.jobs.snapshot()
                self.emit("; ".join(j["label"] + ": " + j["status"] for j in jobs[-5:]) or "No jobs yet.")
                return
            if normalized in {"private mode", "private mode off"}:
                self.private = normalized == "private mode"
                if self.private:
                    self.history.clear()
                self.emit("Private mode " + ("on. Task output is still saved; raw audio and conversation are not." if self.private else "off."))
                return
            if normalized == "forget all memories":
                self.memory.clear()
                self.emit("Saved preferences cleared.")
                return
            if self.pending is not None and not self.pending.done():
                self.emit("I'm still processing the previous request. You can ask for status or stop.")
                return
            ticket = self.generation
            self.pending = self.pool.submit(self._reason, text, ticket, allow_actions)

    def _reason(self, text, ticket, allow_actions):
        reminder = threading.Timer(8, lambda: self._progress(ticket))
        reminder.start()
        try:
            response = self.model.reply(text, {"owner": self.config.owner,
                "memories": [] if self.private else self.memory.list(),
                "conversation": list(self.history), "jobs": self.jobs.snapshot(),
                "authorized_networks": self.config.allowed_networks})
            with self.lock:
                if ticket != self.generation or self.closed.is_set():
                    return
                action = response.get("action")
                if action and not allow_actions:
                    result = "Voice action execution is disabled in this alpha until you explicitly enable it in setup."
                elif action:
                    if action.get("type") == "remember" and "remember" not in text.lower():
                        result = "Please explicitly ask me to remember that preference."
                    else:
                        result = self.actions.execute(action, self.private)
                else:
                    result = response["say"][:1500]
                if not self.private:
                    self.history = (self.history + [{"user": text, "captain": result}])[-6:]
                self.emit(result)
        except Exception as exc:
            with self.lock:
                if ticket == self.generation and not self.closed.is_set():
                    self.emit("I couldn't complete that request: " + str(exc)[:200])
        finally:
            reminder.cancel()

    def _progress(self, ticket):
        if ticket == self.generation and not self.closed.is_set():
            self.emit("I'm still processing your request. Status and stop controls are available.")

    def close(self):
        self.closed.set()
        self.generation += 1
        self.silence()
        self.jobs.close()
        self.pool.shutdown(wait=False, cancel_futures=True)
