"""
Geração da narração (áudio) e das legendas (.srt) sincronizadas via Edge TTS (gratuito).
Edge TTS expõe os eventos de WordBoundary, então as legendas saem com timing preciso.
"""
import asyncio
from pathlib import Path
from rich.console import Console

console = Console()


async def _synthesize(text: str, voice: str, audio_path: Path, srt_path: Path) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice)
    submaker = edge_tts.SubMaker()
    use_feed = hasattr(submaker, "feed")

    with open(audio_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                if use_feed:
                    submaker.feed(chunk)                       # edge-tts >= 7
                else:
                    submaker.create_sub(                       # edge-tts < 7
                        (chunk["offset"], chunk["duration"]), chunk["text"]
                    )

    srt = submaker.get_srt() if hasattr(submaker, "get_srt") else submaker.generate_subs()
    Path(srt_path).write_text(srt, encoding="utf-8")


def synthesize(text: str, voice: str, audio_path: Path, srt_path: Path) -> tuple[Path, Path]:
    """Gera o áudio (.mp3) e a legenda (.srt). Retorna (audio_path, srt_path)."""
    audio_path = Path(audio_path)
    srt_path = Path(srt_path)
    audio_path.parent.mkdir(parents=True, exist_ok=True)

    console.print(f"[cyan]Gerando narração com voz {voice}...[/cyan]")
    asyncio.run(_synthesize(text, voice, audio_path, srt_path))
    console.print(f"[green]Narração: {audio_path.name} | Legenda: {srt_path.name}[/green]")
    return audio_path, srt_path
