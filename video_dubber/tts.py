"""
Text-to-Speech (TTS) module supporting Microsoft Edge-TTS and VieNeu-TTS (Adam Tốp Tốp)
"""
import asyncio
import logging
from pathlib import Path
from typing import List
from .transcriber import Segment

logger = logging.getLogger(__name__)


class TTSService:
    def __init__(
        self,
        voice: str = "vieneu:Adam",
        rate: str = "+0%",
        volume: str = "+0%",
    ):
        self.voice = voice
        self.rate = rate
        self.volume = volume

    async def _generate_single_audio_edge(
        self,
        text: str,
        output_file: Path,
        voice: str,
        rate: str,
        volume: str,
    ) -> bool:
        import edge_tts
        from pydub import AudioSegment
        from .vieneu_tts import enhance_vocal

        output_file.parent.mkdir(parents=True, exist_ok=True)
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            volume=volume,
        )
        await communicate.save(str(output_file))
        if output_file.exists() and output_file.stat().st_size > 0:
            try:
                snd = AudioSegment.from_file(str(output_file))
                snd = enhance_vocal(snd, voice_name=voice, deep_warmth=True)
                fmt = "mp3" if output_file.suffix.lower() == ".mp3" else "wav"
                if fmt == "mp3":
                    snd.export(str(output_file), format="mp3", bitrate="320k")
                else:
                    snd.export(str(output_file), format=fmt)
            except Exception as e_master:
                logger.warning(f"Edge TTS mastering note: {e_master}")
            return True
        return False

    def generate_speech_for_segments(
        self,
        segments: List[Segment],
        output_dir: Path,
    ) -> List[Segment]:
        output_dir.mkdir(parents=True, exist_ok=True)

        is_vieneu = self.voice.startswith("vieneu:") or (not self.voice.endswith("Neural") and "Neural" not in self.voice)

        logger.info(
            f"Generating TTS speech for {len(segments)} segments using voice: {self.voice} (Engine: {'VieNeu-TTS' if is_vieneu else 'Edge-TTS'})..."
        )

        if is_vieneu:
            from .vieneu_tts import generate_vieneu_speech
            clean_voice = self.voice.replace("vieneu:", "")

            for seg in segments:
                text = seg.translated_text.strip() or seg.text.strip()
                if not text:
                    continue
                audio_file = output_dir / f"seg_{seg.id:04d}.wav"
                generate_vieneu_speech(text, voice=clean_voice, output_path=audio_file)
                seg.tts_audio_path = str(audio_file)
        else:
            # Edge TTS (Async concurrent)
            async def run_edge_batch():
                tasks = []
                for seg in segments:
                    text = seg.translated_text.strip() or seg.text.strip()
                    if not text:
                        continue
                    audio_file = output_dir / f"seg_{seg.id:04d}.mp3"
                    seg.tts_audio_path = str(audio_file)
                    task = self._generate_single_audio_edge(
                        text=text,
                        output_file=audio_file,
                        voice=self.voice,
                        rate=self.rate,
                        volume=self.volume,
                    )
                    tasks.append(task)
                await asyncio.gather(*tasks, return_exceptions=True)

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import nest_asyncio
                    nest_asyncio.apply()
                    loop.run_until_complete(run_edge_batch())
                else:
                    loop.run_until_complete(run_edge_batch())
            except RuntimeError:
                asyncio.run(run_edge_batch())

        logger.info("Speech generation finished.")
        return segments

    def generate_speech(
        self,
        segments: List[Segment],
        output_dir: Path,
    ) -> List[Segment]:
        return self.generate_speech_for_segments(segments, output_dir)
