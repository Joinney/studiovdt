"""
VieNeu-TTS Integration Module (High-Fidelity Turbo & Nano with Auto-Fallback)
Seamlessly handles voice compatibility so 'Voice not found' errors never occur.
"""
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from pydub import AudioSegment

logger = logging.getLogger(__name__)

_VIENEU_TURBO_INSTANCE = None
_VIENEU_NANO_INSTANCE = None

# Comprehensive 50+ Emotion and Sound FX Dictionary
EMOTION_SOUND_MAP: Dict[str, str] = {
    # Native tokens for VieNeu neural acoustic cues
    "chuckles": "[cười]",
    "chuckle": "[cười]",
    "cười": "[cười]",
    "cuoi": "[cười]",
    "sighs": "[thở dài]",
    "sigh": "[thở dài]",
    "thở dài": "[thở dài]",
    "tho dai": "[thở dài]",
    "clears throat": "[hắng giọng]",
    "clear throat": "[hắng giọng]",
    "hắng giọng": "[hắng giọng]",
    "hang giong": "[hắng giọng]",

    # Sound FX & Emotional Vocalizations
    "crying": "hu hu... ",
    "khóc": "hu hu... ",
    "coughs": "khụ khụ... ",
    "ho": "khụ khụ... ",
    "lip smacks": "chẹp chẹp... ",
    "annoyed": "chậc! ",
    "screaming": "áaaaa! ",
    "hét": "áaaaa! ",
    "yelling": "Êeeee! ",
    "la hét": "Êeeee! ",
    "affirmative": "ừ hứ, ",
    "realization": "ôooo, ",
    "nhận ra": "ôooo, ",
    "giggles": "hí hí hí ",
    "cười khúc khích": "hí hí hí ",
    "thinking": "hmmm... ",
    "suy nghĩ": "hmmm... ",
    "gasps": "hự! ",
    "excited": "wowww! ",
    "hào hứng": "wowww! ",
    "relieved": "phùuu... ",
    "thở phào": "phùuu... ",
    "confused": "hả? ",
    "bối rối": "hả? ",
    "agreeing": "đúng rồi! ",
    "đồng ý": "đúng rồi! ",
    "cheering": "yeahhhh! ",
    "cổ vũ": "yeahhhh! ",
    "groans": "ôi trời ơi... ",
    "rên rỉ": "ôi trời ơi... ",
    "embarrassed": "ôi ngại quá! ",
    "ngại ngùng": "ôi ngại quá! ",
    "angry": "tức quá! ",
    "tức giận": "tức quá! ",
    "curious": "ủa? ",
    "tò mò": "ủa? ",
    "sarcastic": "ghê chưa! ",
    "mỉa mai": "ghê chưa! ",
    "happy": "vui quá! ",
    "vui vẻ": "vui quá! ",
    "celebrating": "yooooo! ",
    "ăn mừng": "yooooo! ",
    "pleading": "làm ơn đi... ",
    "năn nỉ": "làm ơn đi... ",
    "confident": "chắc chắn luôn! ",
    "tự tin": "chắc chắn luôn! ",
    "grunts": "hự! Cố lên! ",
    "gắng sức": "hự! Cố lên! ",
    "snickers": "khì khì ",
    "cười khẩy": "khì khì ",
    "panicked": "chết chết chết! ",
    "hoảng loạn": "chết chết chết! ",
    "sneezes": "ách xì! ",
    "hắt xì": "ách xì! ",
    "hesitant": "ừm... ",
    "ngập ngừng": "ừm... ",
    "shouting": "gôôôôô! ",
    "surprised": "á há! ",
    "ngạc nhiên": "á há! ",
    "awkward laugh": "hơ hơ hơ... ",
    "cười gượng": "hơ hơ hơ... ",
    "laughing": "hahaha ",
    "cười lớn": "hahaha ",
    "yawns": "ngáppp... ",
    "ngáp": "ngáppp... ",
    "whispering": "psst... ",
    "thì thầm": "psst... ",
    "shocked": "trời ơi! ",
    "sốc": "trời ơi! ",
    "amazed": "ôi wow! ",
    "kinh ngạc": "ôi wow! ",
    "frustrated": "trời đất ơi! ",
    "bực bội": "trời đất ơi! ",
    "doubtful": "thật không vậy? ",
    "nghi ngờ": "thật không vậy? ",
    "disagreeing": "không đâu! ",
    "không đồng ý": "không đâu! ",
    "applause": "bốp bốp bốp! ",
    "vỗ tay": "bốp bốp bốp! ",
    "nervous laugh": "hơ hơ... ",
    "cười trừ": "hơ hơ... ",
    "disappointed": "ôi thôi rồi... ",
    "thất vọng": "ôi thôi rồi... ",
    "worried": "chết rồi! ",
    "lo lắng": "chết rồi! ",
    "teasing": "ê nhaaa! ",
    "trêu chọc": "ê nhaaa! ",
    "proud": "tuyệt vời! ",
    "tự hào": "tuyệt vời! ",
    "sad": "buồn ghê... ",
    "buồn": "buồn ghê... ",
    "apologetic": "anh xin lỗi nhé... ",
    "xin lỗi": "anh xin lỗi nhé... ",
    "determined": "nhất định rồi! ",
    "quyết tâm": "nhất định rồi! ",
    "excited gasp": "ôiiii không! ",
    "smug": "biết ngay mà! ",
    "đắc ý": "biết ngay mà! ",

    # Dramatic Pauses
    "nghỉ 0.5s": "... ",
    "nghỉ 1s": "...... ",
    "nhấn mạnh": "... chính xác là! ",
    "sửng sốt": "hả?! ... ",
}


def preprocess_emotion_text(text: str) -> str:
    def replacer(match):
        raw_tag = match.group(1).strip().lower()
        if raw_tag in EMOTION_SOUND_MAP:
            return EMOTION_SOUND_MAP[raw_tag]
        return f"[{match.group(1)}]"

    processed = re.sub(r"\[([^\]]+)\]", replacer, text)
    processed = re.sub(r"\s+", " ", processed).strip()
    return processed


def change_tempo(sound: AudioSegment, speed: float = 1.0) -> AudioSegment:
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
    global _VIENEU_TURBO_INSTANCE, _VIENEU_NANO_INSTANCE
    from vieneu import Vieneu

    if mode == "v3turbo":
        if _VIENEU_TURBO_INSTANCE is None:
            try:
                logger.info("Initializing VieNeu-TTS Turbo...")
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
    engine = get_vieneu_engine()
    return engine.list_preset_voices()


def generate_vieneu_speech(
    text: str,
    voice: str = "Adam",
    speed: float = 1.0,
    output_path: Union[str, Path] = "output.wav",
) -> Path:
    """
    Synthesizes speech with robust voice fallback so 'Voice not found' never throws.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    clean_voice = voice.replace("vieneu:", "").strip()
    if not clean_voice:
        clean_voice = "Adam"

    # Preprocess emotion cues
    processed_text = preprocess_emotion_text(text)

    # Get active engine
    engine = get_vieneu_engine(mode="v3turbo")

    # Safe Voice Resolution: if selected voice not in active engine, auto-resolve safely!
    available_preset_ids = [vid for _, vid in engine.list_preset_voices()]
    if clean_voice not in available_preset_ids:
        logger.info(f"Voice '{clean_voice}' not found in active engine presets. Resolving fallback...")
        if "adam" in clean_voice.lower() and "Adam" in available_preset_ids:
            clean_voice = "Adam"
        elif available_preset_ids:
            clean_voice = available_preset_ids[0]
        else:
            clean_voice = "Adam"

    logger.info(f"Synthesizing text with VieNeu voice '{clean_voice}' (speed={speed:.2f}x)...")

    try:
        audio = engine.infer(processed_text, voice=clean_voice, steps=16)
    except TypeError:
        audio = engine.infer(processed_text, voice=clean_voice)

    temp_wav = output_path.with_suffix(".tmp.wav")
    engine.save(audio, str(temp_wav))

    # Apply tempo speedup
    sound = AudioSegment.from_wav(str(temp_wav))
    if abs(speed - 1.0) >= 0.03:
        sound = change_tempo(sound, speed=speed)

    fmt = "mp3" if output_path.suffix.lower() == ".mp3" else "wav"
    sound.export(str(output_path), format=fmt)

    try:
        temp_wav.unlink(missing_ok=True)
    except Exception:
        pass

    return output_path
