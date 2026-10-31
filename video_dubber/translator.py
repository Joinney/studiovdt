"""
Text Translation module supporting Deep-Translator (Google Translate) and extensible to LLMs
"""
import logging
from typing import List
from .transcriber import Segment

logger = logging.getLogger(__name__)


class Translator:
    def __init__(self, target_lang: str = "vi", source_lang: str = "auto"):
        self.target_lang = target_lang.lower()
        self.source_lang = source_lang.lower()

    def translate_segments(self, segments: List[Segment]) -> List[Segment]:
        """
        Translates text of each segment to the target language.
        """
        if not segments:
            return segments

        # If source and target are the same, no translation needed
        if self.source_lang == self.target_lang:
            logger.info("Source and target languages are identical. Skipping translation.")
            for seg in segments:
                seg.translated_text = seg.text
            return segments

        try:
            from deep_translator import GoogleTranslator
            translator = GoogleTranslator(
                source=self.source_lang if self.source_lang != "auto" else "auto",
                target=self.target_lang,
            )
        except ImportError:
            raise ImportError("Please install deep-translator via: pip install deep-translator")

        logger.info(f"Translating {len(segments)} segments to '{self.target_lang}'...")
        
        for seg in segments:
            clean_text = seg.text.strip()
            if not clean_text:
                seg.translated_text = ""
                continue
            try:
                translated = translator.translate(clean_text)
                seg.translated_text = translated if translated else clean_text
            except Exception as e:
                logger.warning(f"Failed to translate segment [{seg.id}]: '{clean_text}'. Error: {e}")
                seg.translated_text = clean_text

        logger.info("Translation completed successfully.")
        return segments
