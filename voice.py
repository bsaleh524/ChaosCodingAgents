"""Voice I/O — TTS via `say`, mic recording via sounddevice + webrtcvad, STT via faster-whisper."""

import subprocess
import sys
import tempfile
from pathlib import Path


# ── Text-to-speech ────────────────────────────────────────────────────────────

def say(text: str, enabled: bool = False) -> None:
    if not enabled or sys.platform != "darwin":
        return
    clean = text.replace('"', "'").replace("\n", " ")
    subprocess.run(["say", clean], check=False)


def say_as(agent_name: str, text: str, enabled: bool = False) -> None:
    voices = {"EDGEWORTH": "Alex", "SPARKS": "Zoe", "INTERN": "Samantha"}
    voice = voices.get(agent_name.upper(), "Alex")
    if not enabled or sys.platform != "darwin":
        return
    clean = text.replace('"', "'").replace("\n", " ")
    subprocess.run(["say", "-v", voice, clean], check=False)


# ── Microphone recording + VAD ────────────────────────────────────────────────

def record_until_silence(
    sample_rate: int = 16_000,
    silence_duration_s: float = 1.5,
    max_duration_s: float = 30.0,
) -> bytes:
    """
    Records from the default microphone using sounddevice + webrtcvad.
    Returns raw PCM bytes (16-bit, mono, 16 kHz).
    Stops after `silence_duration_s` of detected silence.
    """
    try:
        import sounddevice as sd
        import numpy as np
        import webrtcvad
    except ImportError:
        raise RuntimeError(
            "Voice recording requires: pip install sounddevice webrtcvad numpy"
        )

    vad = webrtcvad.Vad(2)  # aggressiveness 0-3
    frame_ms = 30
    frame_samples = int(sample_rate * frame_ms / 1000)
    silence_frames_needed = int(silence_duration_s * 1000 / frame_ms)
    max_frames = int(max_duration_s * 1000 / frame_ms)

    frames: list[bytes] = []
    silence_count = 0
    started = False

    with sd.RawInputStream(samplerate=sample_rate, channels=1, dtype="int16") as stream:
        print("  [MIC] Listening... (speak now)")
        for _ in range(max_frames):
            raw, _ = stream.read(frame_samples)
            pcm = bytes(raw)
            frames.append(pcm)
            is_speech = vad.is_speech(pcm, sample_rate)
            if is_speech:
                started = True
                silence_count = 0
            elif started:
                silence_count += 1
                if silence_count >= silence_frames_needed:
                    break

    return b"".join(frames)


# ── Speech-to-text ─────────────────────────────────────────────────────────────

def transcribe(pcm_bytes: bytes, sample_rate: int = 16_000) -> str:
    """Transcribes raw PCM bytes using faster-whisper (base.en model)."""
    try:
        from faster_whisper import WhisperModel
        import numpy as np
    except ImportError:
        raise RuntimeError("STT requires: pip install faster-whisper numpy")

    model = WhisperModel("base.en", device="cpu", compute_type="int8")
    audio = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        _write_wav(f.name, audio, sample_rate)
        segments, _ = model.transcribe(f.name, beam_size=5)
        return " ".join(s.text.strip() for s in segments).strip()


def _write_wav(path: str, audio_f32, sample_rate: int) -> None:
    import wave, struct
    pcm = [struct.pack("<h", max(-32768, min(32767, int(s * 32767)))) for s in audio_f32]
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"".join(pcm))


# ── Convenience: record + transcribe in one shot ──────────────────────────────

def listen() -> str:
    """Record from mic and return transcribed text. Falls back to typed input."""
    try:
        pcm = record_until_silence()
        text = transcribe(pcm)
        print(f"  [TRANSCRIBED] {text}")
        return text
    except RuntimeError as e:
        print(f"  [VOICE UNAVAILABLE] {e}")
        return input("  Type feedback instead: ").strip()
