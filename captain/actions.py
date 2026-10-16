from pathlib import Path
import shutil
import subprocess
import time
from urllib.parse import urlparse
from .policy import Policy, PolicyError


class Actions:
    def __init__(self, config, jobs, memory):
        self.config, self.jobs, self.memory = config, jobs, memory
        self.policy = Policy(config)

    def execute(self, action, private=False):
        if not isinstance(action, dict):
            raise PolicyError("Invalid action")
        kind = action.get("type")
        if kind == "scan":
            target = self.policy.host(action["target"])
            binary = shutil.which("nmap")
            if not binary:
                return "Nmap isn't installed. Installation is not supported by this alpha."
            args = [binary, "-sT", "-sV", "--version-light", "--top-ports", "100",
                    "--host-timeout", str(self.config.job_timeout_seconds) + "s"]
            if ":" in target:
                args += ["-6"]
            args += [target]
            jid = self.jobs.start("Scan " + target, args, self.config.job_timeout_seconds + 10)
            return f"Started scan job {jid} for {target}. I'll report when it finishes."
        if kind == "list_files":
            relative = action.get("path", ".")
            path = self.policy.workspace if relative == "." else self.policy.path(relative)
            return "Files: " + ", ".join(p.name for p in sorted(path.iterdir())[:30])
        if kind == "read_file":
            path = self.policy.path(action["path"])
            if path.stat().st_size > 32768:
                return "That file exceeds this alpha's 32 KB reading limit."
            return path.read_text(encoding="utf-8")
        if kind == "write_file":
            path = self.policy.path(action["path"])
            text = action["text"]
            if not isinstance(text, str) or len(text.encode()) > 32768:
                raise PolicyError("Write exceeds 32 KB limit")
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                backup = self.policy.path(".captain-backups")
                backup.mkdir(mode=0o700, exist_ok=True)
                shutil.copy2(path, backup / (str(time.time_ns()) + "-" + path.name))
            tmp = path.with_name(path.name + ".captain-tmp")
            # Revalidate resolved path before write; workspace must not be writable by untrusted peers.
            self.policy.path(str(tmp))
            with tmp.open("x", encoding="utf-8") as out:
                out.write(text)
            tmp.chmod(0o600)
            tmp.replace(path)
            return f"Saved {path.name}."
        if kind == "remember":
            if private:
                return "Private mode is on. I haven't saved that preference."
            self.memory.add(action["text"])
            return "I've saved that preference."
        if kind == "open_browser":
            url = action.get("url", "about:blank")
            if url != "about:blank" and urlparse(url).scheme not in {"http", "https"}:
                raise PolicyError("Only HTTP or HTTPS browsing is supported.")
            firefox = self.config.firefox_path or shutil.which("firefox")
            if not firefox:
                return "Firefox isn't configured or installed. Set firefox_path in setup."
            subprocess.Popen([firefox, "--new-tab", url], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            return "Requested a new Firefox tab. Page loading has not been verified."
        if kind == "open_terminal":
            binary = next((shutil.which(x) for x in ["qterminal", "xfce4-terminal", "x-terminal-emulator", "wt.exe"] if shutil.which(x)), None)
            if not binary:
                return "No supported terminal application was found."
            subprocess.Popen([binary], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "Requested a terminal window. Numbered window control is not available yet."
        raise PolicyError("That action is not available in this alpha.")
