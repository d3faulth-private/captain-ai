# Acceptance plan

Automated core tests run without downloading models or reaching lab targets.
Hardware acceptance requires the user's actual systems. Record machine configuration,
component versions, trials, median and worst-case delay, failures and recovery.
No invented timings or percentages. A single successful demonstration is insufficient.

| Scenario | Required evidence | Current status |
|---|---|---|
| Nmap/Python job exceeds deadline | Partial output, structured timeout, next job succeeds | Automated Python analogue passes |
| Stop during model computation | Old result cannot execute; clarification immediate | Automated delayed-model test passes |
| Queued and running cancellation | Both reach cancelled, no claimed stop before exit | Automated test passes |
| Out-of-scope target | Reject literal IP outside configured network | Automated test passes |
| Traversal/symlink escape | Reject access outside workspace | Automated test passes |
| File overwrite | New file correct, original preserved | Automated test passes |
| Restart after incomplete task | Mark interrupted, no auto-resume/duplicate | Automated test passes |
| Greeting/name enrollment | Spoken question, repeat back, spoken confirmation | Hardware pending |
| Local request without internet | STT/model/TTS function from cache | Live integration pending |
| Speak while task running | Conversation/status responsive under CPU load | Hardware pending |
| Interrupt while Captain speaks | Reliable detection and promptly silenced audio | Hardware pending |
| Music and other voices | No unintended action; measure false triggers | Not satisfied; echo/auth pending |
| Locked/absent owner | No private output or new GUI action | Not implemented |
| Five terminals / numbered browser tabs | Correct destination after reorder | Not implemented |
| Windows native operation | Real GUI/audio and process-tree cancellation | CI core matrix configured; device pending |
| Full setup / clean machine | Verified components, resumable downloads, readiness | Partial CLI only |
| Watchdog / damaged update | Bounded restart, correct rollback, intentional exit respected | Not implemented |

Before first laptop test: preserve existing ~/captain-kali prototype separately, make a
known-good VM snapshot, use disposable workspace files, keep loopback scope unless a
specific lab target is approved. No deletion of the old prototype is required.
