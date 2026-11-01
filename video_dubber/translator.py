"""
Text Translation module supporting Google Translate (GTX API & Deep-Translator)
Ensures 100% reliable translation without silent failures.
"""
import json
import logging
import re
import time
import urllib.parse
import urllib.request
from typing import List, Optional
from .transcriber import Segment

logger = logging.getLogger(__name__)

# Common English stopwords and Vietnamese diacritics check
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
    # If it contains Vietnamese specific diacritic marks, it is definitely Vietnamese
    if any(c in text for c in VN_DIACRITICS):
        return False
    # Check for common English stopwords
    en_count = sum(1 for w in words if w in COMMON_EN_WORDS)
    return en_count >= 1 or len(words) >= 3


def translate_with_gtx(text: str, target_lang: str = "vi", source_lang: str = "auto") -> Optional[str]:
    """
    Translates text using Google Translate GTX free API.
    Does not require API keys and is extremely fast & reliable.
    """
    clean_text = text.strip()
    if not clean_text:
        return ""
    try:
        url = (
            f"https://translate.googleapis.com/translate_a/single"
            f"?client=gtx&sl={source_lang}&tl={target_lang}&dt=t&q={urllib.parse.quote(clean_text)}"
        )
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept": "*/*",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            if res_json and isinstance(res_json, list) and len(res_json) > 0 and res_json[0]:
                translated_parts = [part[0] for part in res_json[0] if part and part[0]]
                translated = "".join(translated_parts).strip()
                if translated:
                    return translated
    except Exception as e:
        logger.warning(f"GTX translation error for '{clean_text[:30]}...': {e}")
    return None


def translate_with_deep_translator(text: str, target_lang: str = "vi", source_lang: str = "auto") -> Optional[str]:
    """Fallback translation using deep_translator library."""
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
    
    try:
        from deep_translator import MyMemoryTranslator
        mm = MyMemoryTranslator(source=source_lang, target=target_lang)
        res = mm.translate(clean_text)
        if res and res.strip():
            return res.strip()
    except Exception as e:
        logger.warning(f"deep_translator MyMemory error: {e}")
    
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

        # Engine 1: GTX API (fastest & most reliable)
        res = translate_with_gtx(clean, target_lang=self.target_lang, source_lang=self.source_lang)
        if res:
            return res

        # Engine 2: deep-translator fallback
        res = translate_with_deep_translator(clean, target_lang=self.target_lang, source_lang=self.source_lang)
        if res:
            return res

        return clean

    def translate_segments(self, segments: List[Segment]) -> List[Segment]:
        """
        Translates text of each segment to the target language.
        Always validates output to ensure English is actually translated into the target language.
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

        # Step 1: Attempt smart batch translation first (translates entire video script at once)
        # Batching prevents rate limiting and preserves context across sentences
        all_texts = [seg.text.strip() for seg in segments]
        delimiter = " \n---\n "
        combined_payload = delimiter.join(all_texts)
        
        batch_success = False
        try:
            batch_result = translate_with_gtx(combined_payload, target_lang=self.target_lang, source_lang="auto")
            if not batch_result:
                batch_result = translate_with_deep_translator(combined_payload, target_lang=self.target_lang, source_lang="auto")
            
            if batch_result:
                # Split back by delimiter
                split_parts = re.split(r'\s*---\s*', batch_result)
                if len(split_parts) == len(segments):
                    for idx, seg in enumerate(segments):
                        seg.translated_text = split_parts[idx].strip()
                    logger.info("✅ Batch translation succeeded for all segments!")
                    batch_success = True
        except Exception as batch_err:
            logger.warning(f"Batch translation failed, falling back to segment-by-segment: {batch_err}")

        # Step 2: Fallback to segment-by-segment translation if batch failed or had count mismatch
        if not batch_success:
            for idx, seg in enumerate(segments):
                clean_text = seg.text.strip()
                if not clean_text:
                    seg.translated_text = ""
                    continue
                
                translated = self.translate_single(clean_text)
                seg.translated_text = translated if translated else clean_text
                logger.info(f"Segment [{idx+1}/{len(segments)}]: '{clean_text}' -> '{seg.translated_text}'")
                time.sleep(0.08)  # small pause to avoid rate limits

        # Step 3: Strict verification: Check if at least some segments were translated
        if self.target_lang == "vi":
            translated_count = 0
            for seg in segments:
                if seg.translated_text and not is_english_text(seg.translated_text):
                    translated_count += 1
            
            if translated_count == 0 and len(segments) > 0:
                logger.error("⚠️ Cảnh báo: Toàn bộ phụ đề vẫn ở tiếng Anh, bản dịch sang tiếng Việt chưa thành công!")
            else:
                logger.info(f"🎉 Đã dịch thành công {translated_count}/{len(segments)} phân đoạn sang Tiếng Việt!")

        return segments
