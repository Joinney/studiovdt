"""
Configuration and constants for Video Dubber & Text-to-Speech Studio
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union

# Extensive Voices Catalog categorized by Language and Engine
VOICES_CATALOG: Dict[str, Dict[str, str]] = {
    "vi": {
        # 🔥 Giọng Tuyển Chọn Hàng Đầu (Hot / Review / Tốp Tốp)
        "🔥 Adam bựa (VieNeu - Review Phim Tốp Tốp dí dỏm, hài hước)": "vieneu:Adam bựa",
        "🔥 Adam (VieNeu - Giọng Tốp Tốp Tự Nhiên & Đa Cảm Xúc)": "vieneu:Adam",
        "🔥 Hải Đăng (VieNeu - Nam Bắc chuẩn phát thanh, tin tức)": "vieneu:Hải Đăng",
        "🔥 Trúc Ly (VieNeu - Nữ Bắc tự nhiên, trẻ trung, dễ thương)": "vieneu:Trúc Ly",
        "🔥 Thiện Minh (VieNeu - Nam Bắc kể chuyện, sâu lắng, truyền cảm)": "vieneu:Thiện Minh",
        "🔥 Mai Anh (VieNeu - Nữ Bắc tin tức, thời sự chuyên nghiệp)": "vieneu:Mai Anh",
        "🔥 Thùy Dung (VieNeu - Nữ Nam ngọt ngào, nhẹ nhàng)": "vieneu:Thùy Dung",
        "🔥 Thiền Tâm Đức (VieNeu - Nam Bắc trầm tĩnh, triết lý, thiền định)": "vieneu:Thiền Tâm Đức",
        "🔥 Ngọc Huyền (VieNeu - Nữ Bắc kể chuyện, diễn cảm)": "vieneu:Ngọc Huyền",
        "🔥 Quang Sơn (VieNeu - Nam Trung trầm ấm, chân chất)": "vieneu:Quang Sơn",
        "🔥 Ngọc Trân (VieNeu - Nữ Trung đằm thắm, dịu dàng)": "vieneu:Ngọc Trân",

        # 🎙️ Giọng Miền Bắc Đặc Sắc (VieNeu-TTS)
        "Minh Đức (VieNeu - Nam Bắc chững chạc, tin tức)": "vieneu:Minh Đức",
        "Phạm Tuyên (VieNeu - Nam Bắc trầm ấm, tự nhiên)": "vieneu:Phạm Tuyên",
        "Xuân Vĩnh (VieNeu - Nam Bắc tự sự, truyền thống)": "vieneu:Xuân Vĩnh",
        "Thanh Bình (VieNeu - Nam Bắc điềm đạm, ấm áp)": "vieneu:Thanh Bình",
        "Ngọc Linh (VieNeu - Nữ Bắc trong sáng, hoạt bát)": "vieneu:Ngọc Linh",
        "Đoan Trang (VieNeu - Nữ Bắc trang nhã, thanh lịch)": "vieneu:Đoan Trang",
        "Quỳnh Anh (VieNeu - Nữ Bắc nhẹ nhàng, tự nhiên)": "vieneu:Quỳnh Anh",
        "Quốc Tuấn (VieNeu - Nam Bắc khỏe khoắn, đĩnh đạc)": "vieneu:Quốc Tuấn",
        "Ái Hân (VieNeu - Nữ Bắc nhẹ nhàng, truyền cảm)": "vieneu:Ái Hân",
        "Hữu Quân (VieNeu - Nam Bắc phóng khoáng, tự do)": "vieneu:Hữu Quân",
        "Xuân Tiên (VieNeu - Nữ Bắc dễ thương, tươi trẻ)": "vieneu:Xuân Tiên",
        "Anh Khôi (VieNeu - Nam Bắc trẻ trung, năng động)": "vieneu:Anh Khôi",
        "Minh Quân (VieNeu - Nam Bắc điềm đạm, tin cậy)": "vieneu:Minh Quân",
        "Mạnh Dũng (VieNeu - Nam Bắc mạnh mẽ, dứt khoát)": "vieneu:Mạnh Dũng",

        # 🎙️ Giọng Miền Nam Đặc Sắc (VieNeu-TTS)
        "Thái Sơn (VieNeu - Nam Nam hào sảng, hiện đại)": "vieneu:Thái Sơn",
        "Thục Đoan (VieNeu - Nữ Nam duyên dáng, truyền cảm)": "vieneu:Thục Đoan",
        "Minh Triết (VieNeu - Nam Nam trí thức, đĩnh đạc)": "vieneu:Minh Triết",
        "Mỹ Duyên (VieNeu - Nữ Nam đọc truyện tình cảm, ngọt ngào)": "vieneu:Mỹ Duyên",
        "Đức Trí (VieNeu - Nam Nam đọc truyện trinh thám, lôi cuốn)": "vieneu:Đức Trí",
        "Kim Thanh (VieNeu - Nữ Nam tươi sáng, hoạt bát)": "vieneu:Kim Thanh",

        # 🌟 Giọng Tuyển Chọn Mới từ V-TTS (Zero-Shot & Multi-Speaker)
        "Hoàng Nam (V-TTS - Nam Bắc truyền cảm, đọc truyện & phóng sự)": "vieneu:Hoàng Nam",
        "Ngọc Ánh (V-TTS - Nữ Bắc thanh lịch, tin tức & thuyết minh)": "vieneu:Ngọc Ánh",
        "Quang Huy (V-TTS - Nam Nam trầm ấm, hào sảng)": "vieneu:Quang Huy",
        "Thanh Tâm (V-TTS - Nữ Nam dịu dàng, podcast ngọt ngào)": "vieneu:Thanh Tâm",
        "Thu Hà (V-TTS - Nữ Bắc tự nhiên, quảng cáo & lồng tiếng)": "vieneu:Thu Hà",
        "NF - Nữ Bắc (V-TTS - Nữ miền Bắc nguyên bản)": "vieneu:NF",
        "SF - Nữ Nam (V-TTS - Nữ miền Nam nguyên bản)": "vieneu:SF",
        "NM1 - Nam Bắc 1 (V-TTS - Nam miền Bắc chính luận)": "vieneu:NM1",
        "SM - Nam Nam (V-TTS - Nam miền Nam hào sảng)": "vieneu:SM",
        "NM2 - Nam Bắc 2 (V-TTS - Nam miền Bắc trẻ trung)": "vieneu:NM2",

        # ⚡ Giọng Microsoft Edge-TTS (Tốc độ cao)
        "vi-VN-HoaiMyNeural (Edge - Nữ truyền cảm, tin tức)": "vi-VN-HoaiMyNeural",
        "vi-VN-NamMinhNeural (Edge - Nam trầm ấm, chuyên nghiệp)": "vi-VN-NamMinhNeural",
    },
    "en": {
        "en-US-JennyNeural (Nữ - Mỹ, tự nhiên, thân thiện)": "en-US-JennyNeural",
        "en-US-GuyNeural (Nam - Mỹ, tự nhiên, đĩnh đạc)": "en-US-GuyNeural",
        "en-US-AriaNeural (Nữ - Mỹ, biểu cảm sâu sắc)": "en-US-AriaNeural",
        "en-US-ChristopherNeural (Nam - Mỹ, phát thanh viên, tin tức)": "en-US-ChristopherNeural",
        "en-US-EricNeural (Nam - Mỹ, chuyên nghiệp, đĩnh đạc)": "en-US-EricNeural",
        "en-US-AnaNeural (Nữ - Mỹ, trẻ trung, hoạt bát)": "en-US-AnaNeural",
        "en-GB-SoniaNeural (Nữ - Anh/British, thanh lịch)": "en-GB-SoniaNeural",
        "en-GB-RyanNeural (Nam - Anh/British, chuẩn đài BBC)": "en-GB-RyanNeural",
        "en-AU-NatashaNeural (Nữ - Úc/Australian)": "en-AU-NatashaNeural",
        "en-AU-WilliamNeural (Nam - Úc/Australian)": "en-AU-WilliamNeural",
    },
    "zh": {
        "zh-CN-XiaoxiaoNeural (Nữ - Ấm áp, tiểu thuyết, tin tức)": "zh-CN-XiaoxiaoNeural",
        "zh-CN-YunxiNeural (Nam - Sôi nổi, kể chuyện, review)": "zh-CN-YunxiNeural",
        "zh-CN-YunjianNeural (Nam - Nhiệt huyết, review phim)": "zh-CN-YunjianNeural",
        "zh-CN-XiaoyiNeural (Nữ - Tươi vui, hoạt hình)": "zh-CN-XiaoyiNeural",
        "zh-CN-YunyangNeural (Nam - Phát thanh viên)": "zh-CN-YunyangNeural",
        "zh-TW-HsiaoChenNeural (Nữ - Đài Loan)": "zh-TW-HsiaoChenNeural",
        "zh-HK-HiuMaanNeural (Nữ - Hồng Kông)": "zh-HK-HiuMaanNeural",
    },
    "ja": {
        "ja-JP-NanamiNeural (Nữ - Truyền cảm, tự nhiên)": "ja-JP-NanamiNeural",
        "ja-JP-KeitaNeural (Nam - Ấm áp, nhẹ nhàng)": "ja-JP-KeitaNeural",
        "ja-JP-AoiNeural (Nữ - Tươi tắn, anime)": "ja-JP-AoiNeural",
        "ja-JP-DaichiNeural (Nam - Điềm đạm)": "ja-JP-DaichiNeural",
    },
    "ko": {
        "ko-KR-SunHiNeural (Nữ - Tự nhiên, phim Hàn)": "ko-KR-SunHiNeural",
        "ko-KR-InJoonNeural (Nam - Trầm ấm)": "ko-KR-InJoonNeural",
        "ko-KR-HyunsuNeural (Nam - Hiện đại)": "ko-KR-HyunsuNeural",
    },
    "fr": {
        "fr-FR-DeniseNeural (Nữ - Pháp, thanh lịch)": "fr-FR-DeniseNeural",
        "fr-FR-HenriNeural (Nam - Pháp, truyền cảm)": "fr-FR-HenriNeural",
        "fr-CA-SylvieNeural (Nữ - Pháp Canada)": "fr-CA-SylvieNeural",
    },
    "de": {
        "de-DE-KatjaNeural (Nữ - Đức)": "de-DE-KatjaNeural",
        "de-DE-ConradNeural (Nam - Đức)": "de-DE-ConradNeural",
    },
    "es": {
        "es-ES-ElviraNeural (Nữ - Tây Ban Nha)": "es-ES-ElviraNeural",
        "es-ES-AlvaroNeural (Nam - Tây Ban Nha)": "es-ES-AlvaroNeural",
        "es-MX-DaliaNeural (Nữ - Mexico)": "es-MX-DaliaNeural",
    },
    "th": {
        "th-TH-PremwadeeNeural (Nữ - Thái Lan)": "th-TH-PremwadeeNeural",
        "th-TH-NiwatNeural (Nam - Thái Lan)": "th-TH-NiwatNeural",
    },
    "ru": {
        "ru-RU-SvetlanaNeural (Nữ - Nga)": "ru-RU-SvetlanaNeural",
        "ru-RU-DmitryNeural (Nam - Nga)": "ru-RU-DmitryNeural",
    },
}

DEFAULT_VOICES: Dict[str, Dict[str, str]] = {
    "vi": {
        "adam": "vieneu:Adam",
        "female": "vi-VN-HoaiMyNeural",
        "male": "vi-VN-NamMinhNeural",
    },
    "en": {"female": "en-US-JennyNeural", "male": "en-US-GuyNeural"},
    "ja": {"female": "ja-JP-NanamiNeural", "male": "ja-JP-KeitaNeural"},
    "ko": {"female": "ko-KR-SunHiNeural", "male": "ko-KR-InJoonNeural"},
    "zh": {"female": "zh-CN-XiaoxiaoNeural", "male": "zh-CN-YunxiNeural"},
    "fr": {"female": "fr-FR-DeniseNeural", "male": "fr-FR-HenriNeural"},
    "es": {"female": "es-ES-ElviraNeural", "male": "es-ES-AlvaroNeural"},
    "de": {"female": "de-DE-KatjaNeural", "male": "de-DE-ConradNeural"},
    "th": {"female": "th-TH-PremwadeeNeural", "male": "th-TH-NiwatNeural"},
    "ru": {"female": "ru-RU-SvetlanaNeural", "male": "ru-RU-DmitryNeural"},
}

LANGUAGE_NAMES = {
    "vi": "Tiếng Việt (Vietnamese)",
    "en": "Tiếng Anh (English)",
    "zh": "Tiếng Trung (Chinese)",
    "ja": "Tiếng Nhật (Japanese)",
    "ko": "Tiếng Hàn (Korean)",
    "fr": "Tiếng Pháp (French)",
    "de": "Tiếng Đức (German)",
    "es": "Tiếng Tây Ban Nha (Spanish)",
    "th": "Tiếng Thái (Thai)",
    "ru": "Tiếng Nga (Russian)",
}


@dataclass
class DubbingConfig:
    whisper_model: str = "base"
    device: str = "auto"
    compute_type: str = "int8"
    source_language: str = "auto"
    target_language: str = "vi"
    tts_voice: str = "vieneu:Adam"
    tts_rate: str = "+0%"
    tts_volume: str = "+0%"
    original_audio_volume: float = 0.15
    max_speed_factor: float = 1.35
    min_speed_factor: float = 0.75
    temp_dir: Path = field(default_factory=lambda: Path("./temp"))
    output_dir: Path = field(default_factory=lambda: Path("./output"))
    enable_logo: bool = False
    logo_path: Optional[Union[str, Path]] = None
    logo_x_pct: float = 0.80
    logo_y_pct: float = 0.05
    logo_scale: float = 0.18
    logo_opacity: float = 0.90
    burn_subtitles: bool = True
    subtitle_font_size: int = 28
    subtitle_style: str = "white_outline"
    subtitle_margin_v: int = 35
    enable_floating_watermark: bool = False
    floating_watermark_text: str = "@gocphimcuon"
    floating_watermark_font_size: int = 18
    floating_watermark_opacity: float = 0.30

    def __post_init__(self):
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
