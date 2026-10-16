# Architecture and boundaries

Captain is the visible name. The core is shared across OSs; OS-specific integrations
must be replaceable. An offline installation should support local reasoning and speech.
Internet-dependent tasks must report failures without conflating a target outage with
loss of internet connectivity.

## Current components

- `config.py`: private local settings; loopback scope default; no personal profile in Git.
- `voice.py`: bounded RAM audio queues, capture worker, transcription worker, independent
  speech worker. Transcript activation is temporary, not a wake-word implementation.
- `controller.py`: fast commands, one bounded model request, generation tokens to discard
  stale plans, short RAM conversation context, job completion notices.
- `model.py`: Ollama loopback JSON protocol with timeouts, bounded context/output.
- `actions.py`: explicit adapters; no generated shell evaluation.
- `policy.py`: literal-IP engagement scope and resolved workspace path checks.
- `jobs.py`: queue, process groups, timeout/cancel outcome, logs, checkpoint persistence.
- `memory.py`: explicitly requested preferences. No automatic model retraining.
- `setup.py`: diagnostic report and explicit LLM/STT provisioning.

## Execution design

Model proposals are untrusted. Dispatcher and policy validate them. Shell execution
is disabled; subprocess arguments are arrays. A scan never changes scope based on
model output. Target is a literal IP to avoid DNS rebinding in this initial adapter.
Memory and tool output cannot grant authorization.

`Stop` invalidates pending responses and asks what to stop. It does not terminate an
in-flight HTTP calculation immediately; it prevents that response being acted upon.
Jobs continue until specified. Status does not invoke the LLM. Action dispatch is short
and serialized. Long operations run as managed processes. A pending request blocks a
second general reasoning request; this limitation is reported, not concealed.

On restart, unfinished jobs are marked interrupted with unknown process state. Do not
relaunch automatically or kill remembered PIDs (PID reuse). A future supervisor must
own job identities across restarts and reconcile live processes safely.

## Next components

A trained wake detector, speech activity/echo processing, interruption measurements,
OS lock detection, stronger owner-session checks, per-task permissions, browser and
window registries, media controls, health monitor, independent supervisor and update
rollback. General GUI execution needs a desktop lock/foreground arbitration boundary.
Native Windows and Linux control adapters must be tested separately.

User/system mistakes require evidence-based diagnosis, bounded recovery, verification,
and rollback. A watchdog is not an AI self-repair loop and cannot repair a frozen host.
Authenticating a session does not prove the identity of everyone speaking nearby.

## Installation architecture target

Detect hardware, choose suitable components, disclose download sizes/licenses, obtain
normal OS permissions, download from approved origins, verify checksums, resume interrupted
downloads, run readiness checks, then spoken onboarding. Core installer never claims
ready while STT/TTS/model checks fail. Use a small startup voice for onboarding before
heavy reasoning where practical. Existing compatible installations should be reused.
Current setup CLI is only a partial implementation; no silent elevation or unsigned
installer download. Publishing requires owner approval.
