# Captain

**A local-first, voice-first personal assistant for Linux and Windows.**

This repository contains **v0.2.0a1**, an experimental foundation. It is not the full
Captain described in the product roadmap, not an authenticated autonomous desktop
operator, and not a finished installer. No hardware performance claims have been
validated. See [capabilities](docs/CAPABILITIES.md) before use.

## What works in the core

- Ollama loopback JSON planning, with a constrained action dispatcher.
- Independent queued subprocess jobs, streamed logs, cancellation, deadlines, and
  partial output preservation. A timeout does not crash the controller.
- Fast status/cancel routing independent of model requests. Stale model responses
  cannot launch an action after `stop` invalidates them.
- Literal-IP scope checks for basic Nmap service inspection; default scope is loopback.
- Workspace-limited file listing, reading, and writing with overwrite backups.
- Explicit local preference memory, private mode, RAM-only conversation context.
- Firefox and terminal launching (not numbered tab/window manipulation yet).
- Optional microphone / faster-whisper and Piper workers, transcript activation,
  spoken name enrollment, and bounded audio queues. Hardware testing still required.
- Setup diagnostics and explicit model provisioning; no implicit STT downloads at startup.

The normal interaction target is voice. The console is a developer diagnostic aid,
not a replacement for the voice requirements.

## Development installation

Python 3.11 or newer is required. Create a virtual environment, then install:

```sh
python -m pip install -e '.[voice]'
captain setup --model qwen3:4b
captain doctor
```

Use normal Windows/Kali login and OS permission prompts. Install Ollama separately
from its official distribution and start its local service. Linux audio may require
PortAudio system libraries. No automatic elevated installation is attempted.

Select a Piper English voice, review that voice's model card/license, and download
its `.onnx` and matching `.onnx.json` files from the official Piper voice collection.
Configure the absolute model path:

```sh
captain setup --piper-model /absolute/path/to/voice.onnx
captain setup --download
captain voice
```

`--download` explicitly pulls the selected Ollama model and caches the STT model.
It does not download an arbitrary voice without a license choice. It does not install
Ollama or system packages. It can partially succeed; rerun doctor and the setup step
after addressing the reported failure. Fully automated signed installers are pending.

On Windows, use a Windows path for the voice. If Firefox is not on PATH, configure:

```powershell
captain setup --firefox-path 'C:\Program Files\Mozilla Firefox\firefox.exe'
```

Startup after login is a planned integration, not enabled by these commands.

## Voice alpha limitations

**Speaker verification, trained wake-word detection and acoustic echo cancellation
are not implemented.** The microphone transcribes locally in RAM to detect Captain's
name. This is more expensive than a dedicated wake model. Follow-up conversation has
a short timeout. During speaker overlap, only narrow interruption phrases are accepted.
This is not robust full-duplex conversation and cannot reject all media/replay commands.

Voice actions are disabled by default. To enable them explicitly in a private,
disposable lab session after reading these limitations:

```sh
captain setup --enable-voice-actions
```

There is no claim of owner authentication. Do not use this alpha unattended or around
untrusted speakers. Lock-screen suspension of output/actions is not implemented;
exit Captain before locking or leaving the device. A fully disabled microphone cannot
be unmuted by speech. Use device controls to restart. No raw microphone audio is saved.

## Scope and tools

Allow only your actual authorized lab target; this example is documentation-only:

```sh
captain setup --allow-network 192.0.2.10/32
```

This replaces the configured network list. No network discovery or automatic subnet
expansion occurs. The earlier prototype's IP must not be presumed to identify a target
VM: it may be the Kali host itself. Nmap must already be installed. This alpha has no
exploit, arbitrary shell, elevated execution, deletion, email, payment, or publishing
adapter. Those are not silently simulated.

Files are restricted to the configured workspace. This is an application policy,
not a hardened sandbox against a malicious local user. Keep that directory private.
Backups are in `.captain-backups`; automatic spoken undo is pending.

## Voice controls

- `Hey Captain`: enter conversation.
- `Status` / `What are you doing?`: read the current job states without the model.
- `Stop`: invalidate pending planning, silence speech, ask what to stop. Jobs continue.
- `Stop <job name or ID>`: request cancellation; completion is reported separately.
- `Stop everything`: cancel managed jobs and invalidate planning. Does not kill unrelated apps.
- `Quiet`: silence current/queued speech without cancelling jobs.
- `Resume` / `Never mind`: leave the stop clarification state.
- `Private mode`: no preference writes or conversational context; task output still persists.
- `Forget all memories`: clear saved preference rows (not secure disk erasure).

The process runner does not control browser media yet, so `stop everything` cannot
currently stop independently playing music. The specification requires this later.

## Data and privacy

Default data: `~/.local/share/captain` on Linux, `%LOCALAPPDATA%\Captain` on Windows.
Override with `captain --data-dir PATH ...`. Config, preference database, checkpoints,
and raw tool output stay there, outside the repository. Tool logs may contain sensitive
information: restrict access and delete unneeded logs. Log retention/redaction is pending.
There is no telemetry, cloud-model connection, voice clone, real portrait or secret code
bundled. Codex is a future opt-in adapter, not implemented in this alpha.

## Tests

```sh
python -m unittest discover -s tests -v
```

CI runs core tests on Linux/Windows with Python 3.11/3.12. Core tests use temporary
files and local Python child processes, not real networks, microphones, or models.
They do not certify voice latency, speaker identity, GUI behavior, or Windows packaging.

See [architecture](docs/ARCHITECTURE.md), [roadmap](docs/ROADMAP.md),
[acceptance tests](docs/ACCEPTANCE.md), and [security](docs/SECURITY.md).
