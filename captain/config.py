from dataclasses import dataclass, asdict, field
from pathlib import Path
import json
import os


def data_dir():
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Captain"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "captain"


@dataclass
class Config:
    owner: str = ""
    model: str = "qwen3:4b"
    ollama_url: str = "http://127.0.0.1:11434"
    workspace: str = field(default_factory=lambda: str(data_dir() / "workspace"))
    allowed_networks: list[str] = field(default_factory=lambda: ["127.0.0.1/32", "::1/128"])
    piper_model: str = ""
    stt_model: str = "base.en"
    # No claimed speaker authentication: owner must secure their OS session.
    voice_execution_enabled: bool = False
    session_idle_seconds: int = 25
    max_jobs: int = 2
    job_timeout_seconds: int = 300
    firefox_path: str = ""

    def __post_init__(self):
        import re
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,200}", self.model):
            raise ValueError("Invalid model identifier")
        if not 1 <= self.max_jobs <= 8:
            raise ValueError("max_jobs must be between 1 and 8")
        if not 1 <= self.job_timeout_seconds <= 86400:
            raise ValueError("job_timeout_seconds must be between 1 and 86400")

    @classmethod
    def load(cls, root):
        path = Path(root) / "config.json"
        return cls(**json.loads(path.read_text())) if path.exists() else cls()

    def save(self, root):
        root = Path(root)
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        path = root / "config.json"
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(asdict(self), indent=2))
        temp.chmod(0o600)
        temp.replace(path)
