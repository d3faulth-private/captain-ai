"""Independent process jobs. Timeout is an outcome, never an uncaught exception."""
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import os
import signal
import subprocess
import threading
import time
import uuid

TERMINAL = {"completed", "failed", "cancelled", "timed_out", "interrupted", "stop_failed"}

@dataclass
class Job:
    id: str
    label: str
    status: str = "queued"
    returncode: int | None = None
    started: float | None = None
    finished: float | None = None
    error: str = ""
    output: str = ""


class JobManager:
    def __init__(self, root, max_jobs=2):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.lock = threading.RLock()
        self.slots = threading.Semaphore(max(1, max_jobs))
        self.jobs, self.events, self.processes, self.threads = {}, {}, {}, {}
        for path in self.root.glob("*.json"):
            try:
                job = Job(**json.loads(path.read_text()))
                if job.status not in TERMINAL:
                    job.status = "interrupted"
                    job.error = "Previous controller exited. Process state is unknown; inspect before resuming."
                    self._save(job)
                self.jobs[job.id] = job
            except (ValueError, TypeError, OSError):
                continue

    def _save(self, job):
        p = self.root / (job.id + ".json")
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(asdict(job), indent=2))
        tmp.chmod(0o600)
        tmp.replace(p)

    def start(self, label, argv, timeout=300, cwd=None):
        if not argv or not all(isinstance(x, str) for x in argv):
            raise ValueError("argv must be a nonempty list of strings")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        job = Job(uuid.uuid4().hex[:10], label)
        job.output = str(self.root / (job.id + ".log"))
        with self.lock:
            self.jobs[job.id] = job
            self.events[job.id] = threading.Event()
            self._save(job)
            t = threading.Thread(target=self._run, args=(job, argv, timeout, cwd), daemon=True)
            self.threads[job.id] = t
            t.start()
        return job.id

    def _terminate(self, process):
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                           capture_output=True, timeout=10, check=False)
        else:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                return
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass
            # Reap descendants that ignored TERM even when their parent exited.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        process.wait(timeout=5)

    def _run(self, job, argv, timeout, cwd):
        event = self.events[job.id]
        acquired = False
        process = None
        try:
            while not event.is_set():
                if self.slots.acquire(timeout=.1):
                    acquired = True
                    break
            if event.is_set():
                job.status = "cancelled"
                return
            log = Path(job.output)
            log.touch(mode=0o600)
            with log.open("ab", buffering=0) as output:
                kwargs = {"start_new_session": True} if os.name != "nt" else {
                    "creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
                process = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.DEVNULL,
                    stdout=output, stderr=subprocess.STDOUT, shell=False, **kwargs)
                with self.lock:
                    self.processes[job.id] = process
                    job.status, job.started = "running", time.time()
                    self._save(job)
                deadline = time.monotonic() + timeout
                while process.poll() is None:
                    if event.is_set() or time.monotonic() >= deadline:
                        job.status = "stopping"
                        self._save(job)
                        self._terminate(process)
                        job.status = "cancelled" if event.is_set() else "timed_out"
                        break
                    event.wait(.05)
                job.returncode = process.wait()
                if job.status not in TERMINAL:
                    job.status = "completed" if job.returncode == 0 else "failed"
        except Exception as exc:
            job.error = str(exc)
            job.status = "failed"
            if process is not None and process.poll() is None:
                try:
                    self._terminate(process)
                except Exception as stop_error:
                    job.status = "stop_failed"
                    job.error += "; unable to verify stop: " + str(stop_error)
        finally:
            job.finished = time.time()
            with self.lock:
                self._save(job)
                self.processes.pop(job.id, None)
            if acquired:
                self.slots.release()

    def cancel(self, job_id):
        with self.lock:
            job = self.jobs[job_id]
            if job.status in TERMINAL:
                return False
            self.events[job_id].set()
            return True

    def cancel_all(self):
        for job in self.snapshot():
            if job["status"] not in TERMINAL:
                self.cancel(job["id"])

    def snapshot(self):
        with self.lock:
            return [asdict(j) for j in self.jobs.values()]

    def wait(self, job_id, timeout=10):
        self.threads[job_id].join(timeout)
        return self.jobs[job_id]

    def close(self):
        self.cancel_all()
        for t in list(self.threads.values()):
            t.join(15)
