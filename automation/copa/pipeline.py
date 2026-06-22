"""
Orquestra a produção completa de um vídeo de gol da Copa 2026:
  gol -> prompts/roteiro -> animação (IA ou manual) -> narração+legenda -> composição
"""
from pathlib import Path
from rich.console import Console

from automation.config import BASE_DIR, load_channel_config
from automation.copa.goals import Goal
from automation.copa.content import build_shot_prompts, build_narration, build_title
from automation.copa.animate import generate_clips, collect_manual_clips
from automation.copa.narrate import synthesize
from automation.copa.compose import compose

console = Console()

OUTPUT_DIR = BASE_DIR / "data" / "copa_videos"


def make_goal_video(
    goal: Goal,
    clips_dir: Path | None = None,
    music: Path | None = None,
    output_dir: Path = OUTPUT_DIR,
) -> Path | None:
    """
    Produz o vídeo final de um gol.
    Se clips_dir for informado, usa clipes manuais; senão, gera via fal.ai.
    """
    cfg = load_channel_config("copa2026")
    voice = cfg["video"]["voice"]
    aspect = cfg["video"]["aspect"]
    music_volume = cfg["audio"]["background_music_volume"]

    work = output_dir / goal.slug
    work.mkdir(parents=True, exist_ok=True)

    console.print(f"\n[bold cyan]Produzindo gol: {goal.scorer} ({goal.match}, {goal.minute}min)[/bold cyan]")

    # 1. Animação
    if clips_dir:
        clips = collect_manual_clips(Path(clips_dir))
    else:
        shots = build_shot_prompts(goal)
        clips = generate_clips(shots, work / "clips", aspect)

    if not clips:
        console.print("[red]Produção abortada: nenhuma cena disponível.[/red]")
        return None

    # 2. Narração + legendas
    narration_text = build_narration(goal)
    audio, srt = synthesize(
        narration_text, voice,
        work / "narration.mp3", work / "subtitles.srt",
    )

    # 3. Composição final
    final = output_dir / f"{goal.slug}.mp4"
    result = compose(clips, audio, srt, final, music=music, music_volume=music_volume)
    return result


def title_for(goal: Goal) -> str:
    return build_title(goal)
