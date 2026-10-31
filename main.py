"""
CLI Entry Point for Video Dubbing
"""
import sys
from pathlib import Path
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from config import DubbingConfig, DEFAULT_VOICES
from video_dubber.pipeline import VideoDubberPipeline

console = Console()


@click.command()
@click.option(
    "--input", "-i", "video_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Đường dẫn file video cần lồng tiếng (mp4, mkv, mov...)",
)
@click.option(
    "--target-lang", "-t",
    default="vi",
    help="Ngôn ngữ đích (vi: Tiếng Việt, en: Tiếng Anh, ja: Tiếng Nhật...)",
)
@click.option(
    "--source-lang", "-s",
    default="auto",
    help="Ngôn ngữ gốc của video ('auto' để tự động phát hiện)",
)
@click.option(
    "--voice", "-v",
    default=None,
    help="Tên giọng đọc TTS (VD: vi-VN-HoaiMyNeural, vi-VN-NamMinhNeural, en-US-JennyNeural)",
)
@click.option(
    "--whisper-model", "-m",
    default="base",
    type=click.Choice(["tiny", "base", "small", "medium", "large-v3"]),
    help="Kích cỡ model Whisper để nhận diện giọng nói",
)
@click.option(
    "--bg-volume",
    default=0.15,
    type=float,
    help="Âm lượng nền gốc (0.0: tắt hoàn toàn, 0.15: giữ 15% nhạc nền)",
)
@click.option(
    "--output", "-o",
    default=None,
    type=click.Path(dir_okay=False, path_type=Path),
    help="Đường dẫn file video đầu ra hoàn thiện",
)
def main(
    video_path: Path,
    target_lang: str,
    source_lang: str,
    voice: str,
    whisper_model: str,
    bg_volume: float,
    output: Path,
):
    """
    Công cụ AI tự động lồng tiếng video bằng Python.
    """
    console.rule("[bold cyan]AI Video Dubbing Studio[/bold cyan]")
    console.print(f"[green]Video đầu vào:[/green] {video_path}")
    console.print(f"[green]Ngôn ngữ đích:[/green] {target_lang}")
    console.print(f"[green]Model Whisper:[/green] {whisper_model}")

    # Resolve default voice if not specified
    if not voice:
        lang_voices = DEFAULT_VOICES.get(target_lang, DEFAULT_VOICES.get("vi"))
        voice = lang_voices.get("female", "vi-VN-HoaiMyNeural")

    console.print(f"[green]Giọng đọc TTS:[/green] {voice}")

    cfg = DubbingConfig(
        whisper_model=whisper_model,
        source_language=source_lang,
        target_language=target_lang,
        tts_voice=voice,
        original_audio_volume=bg_volume,
    )

    pipeline = VideoDubberPipeline(cfg)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task("Đang khởi tạo pipeline...", total=100)

        def on_progress(msg: str, frac: float):
            progress.update(task_id, description=msg, completed=int(frac * 100))

        try:
            result_video = pipeline.process(
                video_path=video_path,
                output_path=output,
                progress_callback=on_progress,
            )
            console.rule("[bold green]HOÀN THÀNH THÀNH CÔNG[/bold green]")
            console.print(f"🎉 [bold green]Video hoàn thiện:[/bold green] {result_video}")
            console.print(f"📄 [bold green]File phụ đề đi kèm:[/bold green] {result_video.with_suffix('.srt')}")
        except Exception as e:
            console.rule("[bold red]LỖI XẢY RA[/bold red]")
            console.print(f"[red]{e}[/red]")
            sys.exit(1)


if __name__ == "__main__":
    main()
