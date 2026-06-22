"""
Montagem final via ffmpeg:
  clipes animados  ->  normaliza (1080x1920, 30fps)
                   ->  concatena
                   ->  mixa narração + trilha (trilha abaixada)
                   ->  queima legendas com estilo do canal
                   ->  vídeo 9:16 final, com duração igual à da narração

Requer ffmpeg instalado no sistema.
"""
import shutil
import subprocess
from pathlib import Path
from rich.console import Console

console = Console()

W, H, FPS = 1080, 1920, 30

# Cores ASS no formato &HAABBGGRR (BGR invertido).
# Amarelo #FFD700 -> &H0000D7FF | contorno verde #006400 -> &H00006400
SUBTITLE_STYLE = (
    "FontName=Arial,Fontsize=18,Bold=1,"
    "PrimaryColour=&H0000D7FF,OutlineColour=&H00006400,"
    "BorderStyle=1,Outline=3,Shadow=1,Alignment=2,MarginV=120"
)


def _ffmpeg(args: list[str]) -> None:
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args]
    subprocess.run(cmd, check=True)


def check_ffmpeg() -> bool:
    if shutil.which("ffmpeg") is None:
        console.print("[red]ffmpeg não encontrado. Instale-o antes de compor o vídeo.[/red]")
        return False
    return True


def _normalize(clip: Path, out: Path) -> Path:
    vf = (
        f"scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},fps={FPS},format=yuv420p"
    )
    _ffmpeg(["-i", str(clip), "-vf", vf, "-an",
             "-c:v", "libx264", "-preset", "fast", "-crf", "20", str(out)])
    return out


def _concat(clips: list[Path], work: Path) -> Path:
    normalized = []
    for i, clip in enumerate(clips):
        norm = work / f"norm_{i:02d}.mp4"
        _normalize(clip, norm)
        normalized.append(norm)

    listfile = work / "concat.txt"
    listfile.write_text("".join(f"file '{n.resolve()}'\n" for n in normalized), encoding="utf-8")

    base = work / "base.mp4"
    _ffmpeg(["-f", "concat", "-safe", "0", "-i", str(listfile), "-c", "copy", str(base)])
    return base


def _mix_audio(narration: Path, music: Path | None, out: Path, music_volume: float = 0.15) -> Path:
    if music and Path(music).exists():
        _ffmpeg([
            "-i", str(narration), "-stream_loop", "-1", "-i", str(music),
            "-filter_complex",
            f"[1:a]volume={music_volume}[m];[0:a][m]amix=inputs=2:duration=first:dropout_transition=0[a]",
            "-map", "[a]", "-c:a", "aac", "-b:a", "192k", str(out),
        ])
    else:
        _ffmpeg(["-i", str(narration), "-c:a", "aac", "-b:a", "192k", str(out)])
    return out


def compose(
    clips: list[Path],
    narration: Path,
    srt: Path,
    out_path: Path,
    music: Path | None = None,
    music_volume: float = 0.15,
) -> Path | None:
    """Monta o vídeo final. Retorna o caminho do .mp4 ou None em caso de erro."""
    if not check_ffmpeg():
        return None
    if not clips:
        console.print("[red]Sem clipes para compor.[/red]")
        return None

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    work = out_path.parent / "_work"
    work.mkdir(exist_ok=True)

    console.print("[cyan]Normalizando e concatenando cenas...[/cyan]")
    base = _concat(clips, work)

    console.print("[cyan]Mixando áudio...[/cyan]")
    mixed = _mix_audio(narration, music, work / "audio.m4a", music_volume)

    console.print("[cyan]Queimando legendas e finalizando...[/cyan]")
    # srt path precisa de escape para o filtro do ffmpeg
    srt_escaped = str(srt).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    vf = f"subtitles='{srt_escaped}':force_style='{SUBTITLE_STYLE}'"

    # -stream_loop no vídeo base + -shortest garante que o vídeo cubra toda a narração.
    _ffmpeg([
        "-stream_loop", "-1", "-i", str(base),
        "-i", str(mixed),
        "-vf", vf,
        "-map", "0:v", "-map", "1:a",
        "-shortest",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-pix_fmt", "yuv420p",
        str(out_path),
    ])

    shutil.rmtree(work, ignore_errors=True)
    console.print(f"[bold green]Vídeo final: {out_path}[/bold green]")
    return out_path
