"""Explicit provisioning; running the assistant never silently downloads a model."""
import importlib.util
import json
import platform
import shutil
import urllib.request
from pathlib import Path


def doctor(config, root):
    checks = {
        "platform": platform.platform(), "python": platform.python_version(),
        "disk_free_gib": round(shutil.disk_usage(root).free / 2**30, 1),
        "ollama_executable": bool(shutil.which("ollama")),
        "nmap": bool(shutil.which("nmap")),
        "firefox": bool(config.firefox_path or shutil.which("firefox")),
        "voice_packages": {m: importlib.util.find_spec(m) is not None for m in
                           ["sounddevice", "faster_whisper", "piper", "numpy"]},
        "piper_model": bool(config.piper_model and Path(config.piper_model).is_file()),
        "speaker_authentication": "NOT IMPLEMENTED",
        "echo_cancellation": "NOT IMPLEMENTED",
        "voice_actions_enabled": config.voice_execution_enabled,
    }
    try:
        from .model import Ollama
        Ollama(config)  # validate loopback policy
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(config.ollama_url + "/api/tags", timeout=3) as r:
            checks["ollama_models"] = [m["name"] for m in json.load(r)["models"]]
        checks["selected_model_available"] = config.model in checks["ollama_models"]
    except Exception as exc:
        checks["ollama_error"] = str(exc)
    return checks


def provision(config, root):
    import subprocess
    if not shutil.which("ollama"):
        raise RuntimeError("Install Ollama from its official distribution first. This alpha does not install system runtimes.")
    subprocess.run(["ollama", "pull", config.model], check=True)
    from faster_whisper import WhisperModel
    WhisperModel(config.stt_model, device="cpu", compute_type="int8", cpu_threads=1)
    # A voice must be chosen explicitly after checking its model card/license.
    if not config.piper_model:
        raise RuntimeError("LLM and speech recognition prepared. Choose a licensed Piper voice and configure piper_model; speech output is not ready.")
    print(json.dumps(doctor(config, root), indent=2))
