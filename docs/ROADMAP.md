# Captain product roadmap

## Agreed experience

- Voice-first, hands-free normal use: requests, clarifications, corrections and confirmations.
- Starts after normal OS login; spoken first-run preferred-name enrollment. Never ask age at setup.
- Calm, soft, intelligent, warm, concise, practical, playful when appropriate; accurate about uncertainty.
- Addresses the local owner's chosen name/nickname; conversational style configurable.
- Character birthday/age behavior configurable later; reveal only the specific detail asked.
- Adapt conversational tone cautiously using context; do not claim to know emotions with certainty.
- Independence inside explicitly authorized targets and activity classes; no per-command interruption.
- Meaningful progress, proactive fault reporting, combined completion notices, occasional useful suggestions.
- No invented progress, findings, or success. Process completion is not verified task completion.
- Switch strategies based on evidence and bounded budgets; don't ask the user to perform the work.
- Quiet when user is quiet; optional unfinished-work greeting after return.
- General computer assistant with a red-team/lab specialty, not merely a scan wrapper.

## Milestone 1 — reliable local voice and jobs

Current branch starts this milestone, not completes it. Implement and validate trained
wake phrase, echo cancellation, independent interrupt recognition, follow-up dialogue,
local female voice selection, low-latency response under load, voice setup and readiness.
Support private mode, focus mode, interruptible speech, exact-target spelling/correction.
Measure resource budgets on CPU-only four-vCPU VM and stronger hardware.

Stop semantics: bare stop pauses speaking/planning and asks what to stop; running jobs
continue. Stop named task cancels only it. Stop everything cancels Captain-managed tasks
and media, never unrelated services. Quiet only stops speech. Pause is distinct from
cancel; explain tasks that cannot safely suspend. Verify termination before saying stopped.

## Milestone 2 — desktop and browser workspace

- Native Linux and Windows adapters, standard terminals and Firefox.
- Five terminal windows tiled readably, stable internal IDs, working directories and job status.
- Browser spoken numbers match current left-to-right order; internal IDs survive reorder.
- Distinguish browser and window, e.g. Firefox window two tab three.
- Firefox default. Tor or another browser only on explicit request. Missing app: ask whether
  to install it, without a long list of unsolicited alternatives.
- Remember music platform preference; ask for missing song only; duck/restore volume.
- Multiple tasks, queues, dependencies and conflict arbitration; respect manual mouse/keyboard use.
- User decides Windows host vs Kali VM; no automatic host access through shared folders.
- File recovery/undo, explicit irreversible operations, external-action review where needed.

## Milestone 3 — identity, privacy, resilience

- Owner verification evaluation; voice is a signal, never assumed infallible.
- Optional visible camera use with consent; no covert photographs or bait conversations.
- Minimal local security events; unverified names never become confirmed identities.
- Lock-aware behavior: approved headless work continues, GUI/input-dependent work waits;
  suppress private spoken output while absent/locked. Current alpha must be exited instead.
- OS login remains normal. Spoken unlocking is a separate disposable-lab experiment.
- Passwords outside ordinary memory/logging; accessible authentication/recovery paths.
- Independent supervisor, crash reconciliation, safe recovery mode, tested update rollback.
- Checkpoints, separate backups, VM snapshots before major changes; no duplicate resume.
- Host-side emergency recovery independent of the guest, with an accessible fallback.
- Resource/disk pressure alerts, bounded logs and retention, health and microphone checks.

## Milestone 4 — deeper tasks and learning

- Engagement target AND activity permissions, task evidence and verifiable success criteria.
- Additional scoped security adapters, controlled packet capture, reports, GUI inspection.
- Online research and optional Codex with explicit data-sharing control and secret filtering.
- Research can inform a repair, never authorize itself or disable protective controls.
- Build requested agents with limited inherited permissions and tests.
- Verified lessons with source/context, failures marked as failures, inspect/export/delete memory.
- Actual model training only through a separate evaluated candidate, never implicit from tasks.
- Baseline comparisons and rollback before model or self-code promotion.

## Milestone 5 — avatar and expression (not forgotten)

- Realistic reference appearance: headphones, cyan accents, dark outfit, holographic fade.
- Private user-selected assets; public project has no real person's portrait or voice.
- Lightweight 2D first; blinking, small head movements, status lights, move/hide by voice.
- Detailed lip-sync synchronized to actual audio including interruptions and pauses.
- Smile/teeth appearance awaits user's additional reference; do not invent that reference.
- Consensual custom voice, singing as a separate capability, shayari and additional languages.
- Expressive avatar/voice must never delay listening or task cancellation.

## Distribution

Shared core; separate tested Windows installer and Debian-family package, portable Linux
package later if verified. macOS is a future adapter, not a promised first release.
Model/voice licenses checked per artifact; no mandatory paid APIs. Complete dependency
provisioning, hashes, readiness, optional offline bundle. Only publish approved releases.

## Unresolved design/validation items

Secure hands-free OS authorization/recovery; microphone hardware failure fallback;
owner recognition false accept/reject rates; robust speaker echo/replay resistance;
actual CPU speech latency; final models/voices/licenses; windows control and packaging;
public license choice; avatar rights and final assets. Do not mark solved without evidence.
