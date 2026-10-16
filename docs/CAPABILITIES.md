# Capability ledger — v0.2.0a1

| Capability | Status |
|---|---|
| Job deadlines, cancellation, queue, partial output | Implemented; automated local tests |
| Invalidating stale model actions after stop | Implemented; automated test |
| Literal-IP scope, workspace path boundary | Implemented; automated tests; not an OS sandbox |
| Loopback Ollama structured responses | Implemented; live model integration untested here |
| Local speech recognition and Piper output | Implemented adapter; hardware/dependency integration untested |
| Spoken name enrollment | Implemented; microphone testing pending |
| Background conversation | One model request at a time; status/stop fast paths independent |
| Full-duplex conversation / echo cancellation | Not implemented |
| Dedicated Hey Captain wake-word model | Not implemented; transcript-based activation only |
| Speaker recognition / owner verification | Not implemented; voice actions explicit opt-in |
| Firefox and terminal launch | Implemented; desktop verification pending |
| Five numbered terminals / tiling | Planned |
| Numbered Firefox windows/tabs / music | Planned |
| Local preferences and private mode | Implemented; explicit preferences only |
| Verified task lessons / model training | Planned |
| Avatar, blinking, detailed lip-sync, smile reference | Planned; no personal assets in repository |
| Online research / optional Codex | Planned |
| Red-team tool expansion | Planned; only bounded Nmap inspection implemented |
| Lock-aware output and action suspension | Planned; exit before locking/leaving during alpha |
| Autostart / independent supervisor / rollback | Planned; checkpoint recovery marks unknown jobs interrupted |
| Spoken undo / file deletion | Planned; overwrite backups exist |
| Automated complete installer | Partial setup CLI only |
| Windows EXE / Debian / portable Linux releases | Planned; no downloadable installers yet |
| Voice clone / singing / Hindi | Deferred |
| Voice unlocking | Separate experiment, not implemented; normal OS login required |

This ledger is authoritative over aspirational examples. No unimplemented feature
should be represented as working in release notes or an installer.
