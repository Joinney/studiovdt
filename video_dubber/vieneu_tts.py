"""
VieNeu-TTS Integration Module (High-Fidelity Turbo & Nano)
Supports full set of 50+ emotion and sound cues matching the official acoustic mapping:
- [crying] -> hu hu
- [coughs] -> khụ khụ
- [lip smacks] -> chẹp chẹp
- [annoyed] -> chậc
- [screaming] -> áaaaa
- [yelling] -> Êeeee
- [affirmative] -> ừ hứ
- [realization] -> ôooo
- [giggles] -> hí hí hí
- [thinking] -> hmmm
- [gasps] -> hự
- [excited] -> wowww
- [relieved] -> phùuu
- [confused] -> hả?
- [agreeing] -> đúng rồi
- [cheering] -> yeahhhh
- [groans] -> ôi trời ơi...
- [embarrassed] -> ôi ngại quá
- [angry] -> tức quá
- [curious] -> ủa?
- [sarcastic] -> ghê chưa
- [happy] -> vui quá
- [celebrating] -> yooooo
- [pleading] -> làm ơn đi
- [confident] -> chắc chắn luôn
- [grunts] -> hự! Cố lên
- [snickers] -> khì khì
- [panicked] -> chết chết chết!
- [sneezes] -> ách xì
- [hesitant] -> ừm...
- [chuckles] -> [cười]
- [shouting] -> gôôôôô
- [sighs] -> [thở dài]
- [surprised] -> á há
- [awkward laugh] -> hơ hơ hơ
- [laughing] -> hahaha
- [yawns] -> ngáppp
- [whispering] -> psst...
- [shocked] -> trời ơi!
- [amazed] -> ôi wow
- [frustrated] -> trời đất ơi
- [doubtful] -> thật không vậy?
- [disagreeing] -> không đâu
- [applause] -> bốp bốp bốp
- [nervous laugh] -> hơ hơ...
- [disappointed] -> ôi thôi rồi
- [worried] -> chết rồi
- [teasing] -> ê nhaaa
- [proud] -> tuyệt vời
- [sad] -> buồn ghê
- [apologetic] -> anh xin lỗi nhé
- [determined] -> nhất định rồi
- [excited gasp] -> ôiiii không
- [clears throat] -> [hắng giọng]
- [smug] -> biết ngay mà
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

    # Sound FX & Emotional Vocalizations (Exact mapping from chart)
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
    """
    Transforms [bracketed emotion tags] (e.g. [crying], [sneezes], [sighs], [panicked])
    into appropriate neural phonetic cues or natural vocalizations.
    """
    def replacer(match):
        raw_tag = match.group(1).strip().lower()
        if raw_tag in EMOTION_SOUND_MAP:
            return EMOTION_SOUND_MAP[raw_tag]
        # Keep intact if not in map
        return f"[{match.group(1)}]"

    # Replace bracket tags [tag]
    processed = re.sub(r"\[([^\]]+)\]", replacer, text)
    # Clean up double spaces
    processed = re.sub(r"\s+", " ", processed).strip()
    return processed


def change_tempo(sound: AudioSegment, speed: float = 1.0) -> AudioSegment:
    """
    Adjust audio tempo without changing pitch.
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
    engine = get_vieneu_engine()
    return engine.list_preset_voices()


def generate_vieneu_speech(
    text: str,
    voice: str = "Adam bựa",
    speed: float = 1.0,
    output_path: Union[str, Path] = "output.wav",
) -> Path:
    """
    Synthesizes Vietnamese speech using VieNeu-TTS with tempo adjustment and full 50+ emotion cues.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    clean_voice = voice.replace("vieneu:", "").strip()
    if not clean_voice:
        clean_voice = "Adam bựa"

    # Preprocess text through full 50+ emotion dictionary
    processed_text = preprocess_emotion_text(text)

    engine = get_vieneu_engine(mode="v3turbo")
    logger.info(f"Synthesizing text with VieNeu-TTS voice '{clean_voice}' (speed={speed:.2f}x)...")

    # Use steps=16 for fast high-quality generation
    try:
        audio = engine.infer(processed_text, voice=clean_voice, steps=16)
    except TypeError:
        audio = engine.infer(processed_text, voice=clean_voice)

    temp_wav = output_path.with_suffix(".tmp.wav")
    engine.save(audio, str(temp_wav))

    # Apply speed adjustment if requested
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
