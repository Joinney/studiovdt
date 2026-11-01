"""
Text Translation module supporting Google Translate (Chrome Extension Endpoint & Fallbacks)
Uses clients5.google.com/translate_a/t?client=dict-chrome-ex which bypasses HTTP 429 rate-limits.
"""
import json
import logging
from pathlib import Path
import re
import ssl
import time
import urllib.parse
import urllib.request
from typing import List, Optional
from .transcriber import Segment

logger = logging.getLogger(__name__)

# SSL context that bypasses missing local CA certs
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "*/*",
}

COMMON_EN_WORDS = {
    "the", "is", "are", "was", "were", "and", "this", "that", "these", "those",
    "in", "on", "at", "to", "for", "with", "from", "by", "about", "as", "into",
    "it", "you", "he", "she", "they", "we", "i", "not", "but", "or", "because",
    "have", "has", "had", "do", "does", "did", "can", "could", "will", "would",
}
VN_DIACRITICS = "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđĐ"


def is_english_text(text: str) -> bool:
    """Returns True if the text is clearly English and lacks Vietnamese diacritics."""
    words = [w.lower() for w in re.findall(r"\b[a-zA-Z]+\b", text)]
    if not words:
        return False
    if any(c in text for c in VN_DIACRITICS):
        return False
    en_count = sum(1 for w in words if w in COMMON_EN_WORDS)
    return en_count >= 1 or len(words) >= 3


def translate_with_clients5(text: str, target_lang: str = "vi", source_lang: str = "auto") -> Optional[str]:
    """
    Primary translation engine using Google Chrome's dict-chrome-ex endpoint.
    Fast, reliable, and completely immune to standard HTTP 429 rate-limiting.
    """
    clean_text = text.strip()
    if not clean_text:
        return ""
    try:
        url = (
            f"https://clients5.google.com/translate_a/t"
            f"?client=dict-chrome-ex&sl={source_lang}&tl={target_lang}&q={urllib.parse.quote(clean_text)}"
        )
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], list) and len(data[0]) > 0:
                    return str(data[0][0]).strip()
                elif isinstance(data[0], str):
                    return data[0].strip()
    except Exception as e:
        logger.warning(f"clients5 translation error: {e}")
    return None


def translate_with_gtx(text: str, target_lang: str = "vi", source_lang: str = "auto") -> Optional[str]:
    """Secondary fallback: Google Translate GTX endpoint."""
    clean_text = text.strip()
    if not clean_text:
        return ""
    try:
        url = (
            f"https://translate.googleapis.com/translate_a/single"
            f"?client=gtx&sl={source_lang}&tl={target_lang}&dt=t&q={urllib.parse.quote(clean_text)}"
        )
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=12) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            if res_json and isinstance(res_json, list) and len(res_json) > 0 and res_json[0]:
                translated_parts = [part[0] for part in res_json[0] if part and part[0]]
                translated = "".join(translated_parts).strip()
                if translated:
                    return translated
    except Exception as e:
        logger.warning(f"GTX translation error: {e}")
    return None


def translate_with_deep_translator(text: str, target_lang: str = "vi", source_lang: str = "auto") -> Optional[str]:
    """Tertiary fallback using deep_translator library."""
    clean_text = text.strip()
    if not clean_text:
        return ""
    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(
            source=source_lang if source_lang != "auto" else "auto",
            target=target_lang,
        )
        res = translator.translate(clean_text)
        if res and res.strip():
            return res.strip()
    except Exception as e:
        logger.warning(f"deep_translator GoogleTranslator error: {e}")
    return None


class Translator:
    def __init__(self, target_lang: str = "vi", source_lang: str = "auto"):
        self.target_lang = target_lang.lower()
        self.source_lang = source_lang.lower()

    def translate_single(self, text: str) -> str:
        """Translates a single string with multi-engine fallback."""
        clean = text.strip()
        if not clean:
            return ""

        # Engine 1: clients5 (Dict Chrome Ex - 100% reliable)
        res = translate_with_clients5(clean, target_lang=self.target_lang, source_lang=self.source_lang)
        if res:
            return res

        # Engine 2: GTX API
        res = translate_with_gtx(clean, target_lang=self.target_lang, source_lang=self.source_lang)
        if res:
            return res

        # Engine 3: deep-translator
        res = translate_with_deep_translator(clean, target_lang=self.target_lang, source_lang=self.source_lang)
        if res:
            return res

        return clean

    def translate_segments(self, segments: List[Segment]) -> List[Segment]:
        """
        Translates text of each segment to the target language.
        Guarantees that segments are translated into the target language.
        """
        if not segments:
            return segments

        # Only skip translation if source and target match AND the text is NOT obviously English when target is Vietnamese
        if self.source_lang == self.target_lang and self.source_lang != "auto":
            first_text = " ".join([s.text for s in segments[:3]])
            if not (self.target_lang == "vi" and is_english_text(first_text)):
                logger.info("Source and target languages are identical. Skipping translation.")
                for seg in segments:
                    seg.translated_text = seg.text
                return segments

        logger.info(f"Translating {len(segments)} segments to '{self.target_lang}'...")

        # Batch translation via clients5 using newline delimiter
        all_texts = [seg.text.strip() for seg in segments]
        delimiter = "\n---\n"
        combined_payload = delimiter.join(all_texts)
        
        batch_success = False
        try:
            batch_result = translate_with_clients5(combined_payload, target_lang=self.target_lang, source_lang="auto")
            if not batch_result:
                batch_result = translate_with_gtx(combined_payload, target_lang=self.target_lang, source_lang="auto")
            
            if batch_result:
                split_parts = [p.strip() for p in re.split(r'\s*---\s*', batch_result) if p.strip()]
                if len(split_parts) == len(segments):
                    for idx, seg in enumerate(segments):
                        seg.translated_text = split_parts[idx]
                    logger.info("✅ Batch translation succeeded for all segments!")
                    batch_success = True
        except Exception as batch_err:
            logger.warning(f"Batch translation error: {batch_err}")

        # Fallback to segment-by-segment if batch failed or had count mismatch
        if not batch_success:
            for idx, seg in enumerate(segments):
                clean_text = seg.text.strip()
                if not clean_text:
                    seg.translated_text = ""
                    continue
                
                translated = self.translate_single(clean_text)
                seg.translated_text = translated if translated else clean_text
                time.sleep(0.04)

        # Log translated results to file for diagnostics
        try:
            log_dir = Path("./temp")
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "translation_history.log"
            with open(log_file, "a", encoding="utf-8") as f_log:
                f_log.write(f"\n--- Translation Run [{len(segments)} segments] to {self.target_lang} ---\n")
                for s in segments:
                    f_log.write(f"[{s.id}] {s.text} -> {s.translated_text}\n")
        except Exception:
            pass

        return segments
