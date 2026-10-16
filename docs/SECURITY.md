# Security and operational limits

This alpha is NOT an owner-authenticated unattended agent. Anyone who can speak to the
microphone can potentially issue recognized commands when voice actions are opted in.
Transcript wake detection is not authentication. Recordings and media can trigger it.
Do not place the assistant in a shared/untrusted audio environment. Normal OS locking
remains necessary; the alpha does not yet track OS lock state. Exit it before leaving.

- No elevated service or stored administrator password.
- No arbitrary generated shell commands. Explicit tool adapters only.
- Literal IP allowlist, user-configured workspace, bounded model response.
- Local Ollama only. No optional cloud model is silently activated.
- Raw microphone audio stays in bounded RAM queues; no recordings persisted.
- Task stdout/stderr persists and may contain secrets. No universal redaction guarantee.
- Config and data are outside the Git repository. Protect Windows directory ACLs; POSIX
  chmod alone does not establish Windows ACL isolation.
- Workspace boundary assumes no hostile local process racing symlink/path changes.
  It is not a substitute for OS sandboxing or file ACLs.
- Finished subprocesses can leave detached descendants; supported adapters should not
  daemonize. Cancellation uses process groups on POSIX, taskkill tree termination on
  Windows. Restart checkpoints do not authorize killing arbitrary recycled PIDs.
- All models, code, file/web/tool content and preferences can be wrong. None can enlarge
  engagement scope, disable supervision or authorize external publishing.
- No self-update execution from fetched web advice.
- Resource/log limits, stronger owner verification, package signing, lock detection and
  hardened installer/recovery remain required before general-purpose public deployment.

Do not commit private photos, voiceprints, recordings, access codes, API tokens, reports,
or user profiles. Public repository access is not permission to redistribute a voice,
likeness, model or third-party component. Each asset needs its own license/permission review.
