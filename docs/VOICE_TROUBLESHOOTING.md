# Voice input and latency

The listener measures two seconds of background audio after speech output stops.
Stay quiet until `Microphone ready` appears. The calibrated energy gate preserves
300 ms of preceding audio; Whisper's existing VAD then filters non-speech.
Quiet clips are normalized in RAM before transcription. Raw audio is not saved.
This is not a dedicated low-latency wake-word detector or acoustic echo canceller.

The transcription queue keeps one fresh clip, replacing older pending clips.
Clips waiting longer than three seconds are discarded. Already-running
transcription cannot be interrupted; recognition can still delay stop detection.
If a command is dropped during overload, repeat it after the response finishes.

Voice startup preloads the configured Ollama model in a background thread with
a 10-minute loading timeout. Requests keep the model resident for 30 minutes.
Actual unloading can still occur under memory pressure. Responses allow 180
seconds, capped at 160 generated tokens, and still wait for complete JSON.
Recognition time and model load/generation time are printed for diagnosis.
Long responses can be truncated; this is not a guarantee of low latency.

On the target VM, check normal-volume recognition, quiet-room false triggers,
speaker echo, and stop interruption. Unit tests do not validate actual audio
hardware, recognition accuracy, or end-to-end latency. Voice actions remain
opt-in and owner verification remains unimplemented.
