"""Optional audio workers. All microphone audio is RAM-only.

This alpha uses transcript-based activation, NOT a trained low-power wake model.
Acoustic echo cancellation and speaker verification are not implemented.
"""
from collections import deque
import statistics
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
        self.utterances = queue.Queue(maxsize=1)
        self.closed = threading.Event()
        self.last_addressed = 0

    def _callback(self, data, frames, timing, status):
        try:
            self.frames.put_nowait((time.monotonic(), data[:, 0].copy(), self.speaker_active()))
        except queue.Full:
            pass  # bounded RAM use; no writes in audio callback

    def _decode(self):
        while not self.closed.is_set():
            try:
                captured, audio, overlap = self.utterances.get(timeout=.2)
            except queue.Empty:
                continue
            if time.monotonic() - captured > 3:
                continue
            try:
                # Normalize quiet input in RAM before Whisper's speech detector.
                peak = float(self.np.max(self.np.abs(audio)))
                if peak > 0:
                    audio = audio * min(20.0, .8 / peak)
                started = time.monotonic()
                segments, _ = self.model.transcribe(audio, language="en", beam_size=1,
                                                    vad_filter=True)
                text = " ".join(s.text for s in segments).strip()
                print(f"Recognition: {time.monotonic() - started:.2f}s", flush=True)
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
        pieces, silence, overlap = [], 0, False
        pre_roll = deque(maxlen=6)  # 300 ms preserves quiet word beginnings.
        calibration = []
        threshold = None
        print("Microphone calibration: stay quiet until calibration completes.", flush=True)
        with self.sd.InputStream(samplerate=16000, channels=1, dtype="float32",
                                 blocksize=800, callback=self._callback):
            while not self.closed.is_set():
                try:
                    captured, frame, speaking = self.frames.get(timeout=2)
                except queue.Empty:
                    self.notify("Microphone input stopped. Check the audio device.")
                    break
                if time.monotonic() - captured > 1:
                    pieces, silence, overlap = [], 0, False
                    pre_roll.clear()
                    continue
                level = float(self.np.sqrt(self.np.mean(frame * frame)))
                if threshold is None:
                    # Exclude Captain's greeting from the background measurement.
                    if speaking:
                        calibration.clear()
                        continue
                    calibration.append(level)
                    if len(calibration) >= 40:
                        threshold = calibrated_threshold(calibration)
                        print(f"Microphone ready. Detection threshold: {threshold:.5f}. "
                              "Say Hey Captain. Speaker authentication is unavailable.", flush=True)
                    continue
                loud = level > threshold
                if not pieces:
                    pre_roll.append((frame, speaking))
                    if not loud:
                        continue
                    pieces = [f for f, _ in pre_roll]
                    overlap = any(active for _, active in pre_roll)
                    pre_roll.clear()
                else:
                    pieces.append(frame)
                    overlap = overlap or speaking
                silence = 0 if loud else silence + 1
                if silence >= 12 or len(pieces) >= 160:
                    if len(pieces) > 8:
                        # Keep fresh speech instead of building a stale backlog.
                        put_latest(self.utterances,
                                   (captured, self.np.concatenate(pieces), overlap))
                    pieces, silence, overlap = [], 0, False
        self.closed.set()


def calibrated_threshold(levels):
    """Robust to isolated background clicks; Whisper VAD verifies speech later."""
    return min(.012, max(.00015, statistics.median(levels) * 4))


def put_latest(target, item):
    try:
        target.put_nowait(item)
    except queue.Full:
        try:
            target.get_nowait()
        except queue.Empty:
            pass
        try:
            target.put_nowait(item)
        except queue.Full:
            pass
