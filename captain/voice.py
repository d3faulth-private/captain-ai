"""Optional audio workers. All microphone audio is RAM-only.

This alpha uses transcript-based activation, NOT a trained low-power wake model.
Acoustic echo cancellation and speaker verification are not implemented.
"""
import queue
import threading
import time


class Speaker:
    def __init__(self, model_path):
        import sounddevice as sd
        from piper import PiperVoice
        self.sd = sd
        self.voice = PiperVoice.load(model_path)
        self.queue = queue.Queue(maxsize=8)
        self.generation = 0
        self.active = threading.Event()
        self.closed = threading.Event()
        threading.Thread(target=self._run, daemon=True).start()

    def say(self, text):
        print("Captain:", text, flush=True)
        try:
            self.queue.put_nowait((self.generation, text))
        except queue.Full:
            print("Captain: Speech queue full; see the screen for this update.", flush=True)

    def silence(self):
        self.generation += 1
        while True:
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break

    def _run(self):
        while not self.closed.is_set():
            try:
                ticket, text = self.queue.get(timeout=.2)
            except queue.Empty:
                continue
            if ticket != self.generation:
                continue
            self.active.set()
            try:
                for chunk in self.voice.synthesize(text):
                    if ticket != self.generation:
                        break
                    data = chunk.audio_int16_bytes
                    with self.sd.RawOutputStream(samplerate=chunk.sample_rate, channels=1,
                                                 dtype="int16") as stream:
                        step = max(2, int(chunk.sample_rate * .02) * 2)
                        for start in range(0, len(data), step):
                            if ticket != self.generation or self.closed.is_set():
                                stream.abort()
                                break
                            stream.write(data[start:start + step])
            except Exception as exc:
                print("Speech output failed:", exc, flush=True)
            finally:
                self.active.clear()

    def close(self):
        self.closed.set()
        self.silence()


class Listener:
    def __init__(self, config, on_text, notify, speaker_active=lambda: False):
        import numpy as np
        import sounddevice as sd
        from faster_whisper import WhisperModel
        self.np, self.sd = np, sd
        # No implicit network access when starting Captain.
        self.model = WhisperModel(config.stt_model, device="cpu", compute_type="int8",
                                  cpu_threads=1, local_files_only=True)
        self.config, self.on_text, self.notify = config, on_text, notify
        self.speaker_active = speaker_active
        self.frames = queue.Queue(maxsize=100)
        self.utterances = queue.Queue(maxsize=3)
        self.closed = threading.Event()
        self.last_addressed = 0

    def _callback(self, data, frames, timing, status):
        try:
            self.frames.put_nowait(data[:, 0].copy())
        except queue.Full:
            pass  # bounded RAM use; no writes in audio callback

    def _decode(self):
        while not self.closed.is_set():
            try:
                audio, overlap = self.utterances.get(timeout=.2)
            except queue.Empty:
                continue
            try:
                segments, _ = self.model.transcribe(audio, language="en", beam_size=1,
                                                    vad_filter=True)
                text = " ".join(s.text for s in segments).strip()
                low = text.lower().strip(" .!?,")
                if not low:
                    continue
                addressed = low.startswith(("captain", "hey captain"))
                # While speakers are active accept only explicit Captain stop/quiet.
                # This reduces echo accidents but is NOT replay/owner protection.
                if overlap and low not in {"stop", "quiet", "stop everything", "captain stop", "captain, stop", "captain quiet", "captain, quiet", "captain stop everything", "captain, stop everything"}:
                    continue
                if addressed:
                    self.last_addressed = time.monotonic()
                elif time.monotonic() - self.last_addressed > self.config.session_idle_seconds:
                    continue
                else:
                    self.last_addressed = time.monotonic()
                if low in {"captain", "hey captain"}:
                    self.notify("Yes, " + (self.config.owner or "Boss") + "?")
                elif "stop listening to the conversation" in low or "give me some privacy" in low:
                    self.last_addressed = 0
                    self.notify("I'll wait until you address me again.")
                elif "mute your microphone" in low:
                    self.notify("Muting. Restart Captain using the device controls to enable listening again.")
                    self.closed.set()
                elif not self.config.owner:
                    name = text.removeprefix("My name is ").removeprefix("Call me ").strip(" .")
                    if 1 <= len(name) <= 40:
                        # Enrollment handled by voice_loop with explicit confirmation.
                        self.on_text("__name__ " + name)
                else:
                    self.on_text(text)
            except Exception as exc:
                self.notify("Speech recognition failed. " + str(exc)[:120])

    def run(self):
        threading.Thread(target=self._decode, daemon=True).start()
        pieces, silence, voiced, overlap = [], 0, False, False
        self.notify("Microphone listening. Say Hey Captain. Speaker authentication is not available in this alpha.")
        with self.sd.InputStream(samplerate=16000, channels=1, dtype="float32",
                                 blocksize=800, callback=self._callback):
            while not self.closed.is_set():
                try:
                    frame = self.frames.get(timeout=2)
                except queue.Empty:
                    self.notify("Microphone input stopped. Check the audio device.")
                    break
                loud = float(self.np.sqrt(self.np.mean(frame * frame))) > .012
                if loud or voiced:
                    pieces.append(frame)
                    overlap = overlap or self.speaker_active()
                    voiced = True
                    silence = 0 if loud else silence + 1
                if pieces and (silence >= 12 or len(pieces) >= 240):
                    if len(pieces) > 5:
                        try:
                            self.utterances.put_nowait((self.np.concatenate(pieces), overlap))
                        except queue.Full:
                            self.notify("Speech processing is busy. Please repeat after a moment.")
                    pieces, silence, voiced, overlap = [], 0, False, False
        self.closed.set()
