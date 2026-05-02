"""Voice I/O — TTS via ElevenLabs or Mac `say`, mic via sounddevice + webrtcvad, STT via faster-whisper."""

import subprocess
import sys
import tempfile
from pathlib import Path

import config

# ── ElevenLabs voice IDs ───────────────────────────────────────────────────────
ELEVENLABS_VOICES = {
    "EDGEWORTH": config.EDGEWORTH_VOICE_ID,
    "LIGHT":     config.LIGHT_VOICE_ID,
}

# Mac `say` voice fallbacks
SAY_VOICES = {
    "EDGEWORTH": "Alex",
    "LIGHT":     "Daniel",
    "INTERN":    "Samantha",
}


# ── ElevenLabs TTS ────────────────────────────────────────────────────────────

def _say_elevenlabs(text: str, voice_id: str, api_key: str) -> None:
    try:
        import httpx
    except ImportError:
        raise RuntimeError("ElevenLabs requires httpx: pip install httpx")

    clean = text.replace("\n", " ").strip()
    resp = httpx.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
        json={
            "text": clean,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.45, "similarity_boost": 0.75},
        },
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"  [ELEVENLABS ERROR] {resp.status_code}: {resp.text[:200]}")
        return

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(resp.content)
        tmp_path = f.name

    subprocess.run(["afplay", tmp_path], check=False)
    Path(tmp_path).unlink(missing_ok=True)


# ── Text-to-speech dispatcher ─────────────────────────────────────────────────

def say_as(agent_name: str, text: str, enabled: bool = False) -> None:
    """
    Speak `text` as `agent_name`.
    Priority: ElevenLabs (if USE_ELEVENLABS + key set) → Mac `say` → silent.
    `enabled` must be True for any audio to play.
    """
    if not enabled:
        return

    name = agent_name.upper()

    # ── ElevenLabs path ───────────────────────────────────────────────────────
    if config.USE_ELEVENLABS and config.ELEVENLABS_API_KEY:
        voice_id = ELEVENLABS_VOICES.get(name)
        if voice_id:
            _say_elevenlabs(text, voice_id, config.ELEVENLABS_API_KEY)
            return
        # Agent has no ElevenLabs voice (e.g. Intern) — fall through to say

    # ── Mac say fallback ──────────────────────────────────────────────────────
    if sys.platform != "darwin":
        return
    voice = SAY_VOICES.get(name, "Alex")
    clean = text.replace('"', "'").replace("\n", " ")
    subprocess.run(["say", "-v", voice, clean], check=False)


def say(text: str, enabled: bool = False) -> None:
    if not enabled or sys.platform != "darwin":
        return
    clean = text.replace('"', "'").replace("\n", " ")
    subprocess.run(["say", clean], check=False)


# ── Microphone recording + VAD ────────────────────────────────────────────────

def record_until_silence(
    sample_rate: int = 16_000,
    silence_duration_s: float = 1.5,
    max_duration_s: float = 30.0,
) -> bytes:
    try:
        import sounddevice as sd
        import numpy as np
        import webrtcvad
    except ImportError:
        raise RuntimeError(
            "Voice recording requires: pip install sounddevice webrtcvad numpy"
        )

    vad = webrtcvad.Vad(2)
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


def listen() -> str:
    try:
        pcm = record_until_silence()
        text = transcribe(pcm)
        print(f"  [TRANSCRIBED] {text}")
        return text
    except RuntimeError as e:
        print(f"  [VOICE UNAVAILABLE] {e}")
        return input("  Type feedback instead: ").strip()
