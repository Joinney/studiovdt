"""
VieNeu-TTS Integration Module (High-Fidelity Turbo & Nano)
Supports full set of Adam voices with speed adjustment and emotion tags:
- 'Adam bựa': Nam · Bắc · Phong cách Review phim / Meme TikTok đỉnh cao
- 'Adam': Nam · Nam · Giọng đọc tự nhiên, cuốn hút
"""
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Union
from pydub import AudioSegment

logger = logging.getLogger(__name__)

_VIENEU_TURBO_INSTANCE = None
_VIENEU_NANO_INSTANCE = None


def change_tempo(sound: AudioSegment, speed: float = 1.0) -> AudioSegment:
    """
    Adjust audio tempo without changing pitch.
    speed > 1.0 = faster (e.g. 1.2x)
    speed < 1.0 = slower (e.g. 0.9x)
    """
    if abs(speed - 1.0) < 0.03:
        return sound

    if speed > 1.0:
        from pydub.effects import speedup
        try:
            return speedup(sound, playback_speed=speed)
        except Exception:
            new_frame_rate = int(sound.frame_rate * speed)
            return sound._spawn(sound.raw_data, overrides={"frame_rate": new_frame_rate}).set_frame_rate(sound.frame_rate)
    else:
        new_frame_rate = int(sound.frame_rate * speed)
        return sound._spawn(sound.raw_data, overrides={"frame_rate": new_frame_rate}).set_frame_rate(sound.frame_rate)


def get_vieneu_engine(mode: str = "v3turbo"):
    """
    Singleton getter for Vieneu instance.
    Prefers v3turbo for 48kHz audio and all 25 voices including 'Adam bựa'.
    Falls back to v3nano if turbo fails.
    """
    global _VIENEU_TURBO_INSTANCE, _VIENEU_NANO_INSTANCE
    from vieneu import Vieneu

    if mode == "v3turbo":
        if _VIENEU_TURBO_INSTANCE is None:
            try:
                logger.info("Initializing VieNeu-TTS Turbo (48kHz, 25 preset voices)...")
                _VIENEU_TURBO_INSTANCE = Vieneu(mode="v3turbo")
            except Exception as e:
                logger.warning(f"Failed to initialize VieNeu Turbo ({e}), falling back to v3nano.")
                return get_vieneu_engine(mode="v3nano")
        return _VIENEU_TURBO_INSTANCE
    else:
        if _VIENEU_NANO_INSTANCE is None:
            logger.info("Initializing VieNeu-TTS Nano (24kHz)...")
            _VIENEU_NANO_INSTANCE = Vieneu(mode="v3nano")
        return _VIENEU_NANO_INSTANCE


def list_vieneu_voices() -> List[Tuple[str, str]]:
    """
    Returns list of (label, voice_id) available in VieNeu-TTS.
    """
    engine = get_vieneu_engine()
    return engine.list_preset_voices()


def generate_vieneu_speech(
    text: str,
    voice: str = "Adam bựa",
    speed: float = 1.0,
    output_path: Union[str, Path] = "output.wav",
) -> Path:
    """
    Synthesizes Vietnamese speech using VieNeu-TTS with tempo adjustment.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    clean_voice = voice.replace("vieneu:", "").strip()
    if not clean_voice:
        clean_voice = "Adam bựa"

    engine = get_vieneu_engine(mode="v3turbo")
    logger.info(f"Synthesizing text with VieNeu-TTS voice '{clean_voice}' (speed={speed:.2f}x)...")

    # Use steps=16 for blazing fast generation
    try:
        audio = engine.infer(text, voice=clean_voice, steps=16)
    except TypeError:
        # Fallback if engine doesn't accept steps
        audio = engine.infer(text, voice=clean_voice)

    # Save to temp wav
    temp_wav = output_path.with_suffix(".tmp.wav")
    engine.save(audio, str(temp_wav))

    # Apply speed adjustment if requested
    sound = AudioSegment.from_wav(str(temp_wav))
    if abs(speed - 1.0) >= 0.03:
        sound = change_tempo(sound, speed=speed)

    # Export final file format
    fmt = "mp3" if output_path.suffix.lower() == ".mp3" else "wav"
    sound.export(str(output_path), format=fmt)

    # Cleanup temp
    try:
        temp_wav.unlink(missing_ok=True)
    except Exception:
        pass

    return output_path
