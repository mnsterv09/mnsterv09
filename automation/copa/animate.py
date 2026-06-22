"""
Geração das cenas animadas via modelo de vídeo IA.

Provedor padrão: fal.ai (acesso unificado a Kling, Runway, etc. com uma chave).
Configure FAL_KEY no .env e, opcionalmente, COPA_ANIM_MODEL.

Modo manual: se você gerou os clipes na interface web do Kling/Runway,
basta colocá-los numa pasta e usar collect_manual_clips() — sem custo de API.
"""
import os
import time
import requests
from pathlib import Path
from rich.console import Console

console = Console()

FAL_KEY = os.getenv("FAL_KEY")
# Modelo no fal.ai. Alternativas: fal-ai/runway-gen3/turbo/image-to-video, fal-ai/luma-dream-machine
ANIM_MODEL = os.getenv("COPA_ANIM_MODEL", "fal-ai/kling-video/v2/master/text-to-video")


def _download(url: str, out_path: Path) -> Path:
    resp = requests.get(url, stream=True, timeout=180)
    resp.raise_for_status()
    with open(out_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1 << 16):
            f.write(chunk)
    return out_path


def generate_clip(prompt: str, duration: int, out_path: Path, aspect: str = "9:16", retries: int = 2) -> Path | None:
    """Gera um único clipe via fal.ai e salva em out_path."""
    if not FAL_KEY:
        console.print("[red]FAL_KEY não configurada no .env — não é possível gerar via API.[/red]")
        console.print("[yellow]Use o modo manual (--clips-dir) com clipes gerados na web.[/yellow]")
        return None

    try:
        import fal_client
    except ImportError:
        console.print("[red]Pacote 'fal-client' não instalado. Rode: pip install fal-client[/red]")
        return None

    arguments = {
        "prompt": prompt,
        "duration": str(duration),
        "aspect_ratio": aspect,
    }

    for attempt in range(1, retries + 2):
        try:
            console.print(f"[cyan]Gerando cena ({duration}s, tentativa {attempt})...[/cyan]")
            result = fal_client.subscribe(ANIM_MODEL, arguments=arguments, with_logs=False)
            video_url = result["video"]["url"]
            _download(video_url, out_path)
            console.print(f"[green]Cena pronta: {out_path.name}[/green]")
            return out_path
        except Exception as e:
            console.print(f"[yellow]Falha na tentativa {attempt}: {e}[/yellow]")
            time.sleep(3 * attempt)

    console.print("[red]Não foi possível gerar a cena após as tentativas.[/red]")
    return None


def generate_clips(shots: list[dict], work_dir: Path, aspect: str = "9:16") -> list[Path]:
    """Gera todas as cenas de um gol. Retorna os clipes na ordem das cenas."""
    work_dir.mkdir(parents=True, exist_ok=True)
    clips: list[Path] = []
    for i, shot in enumerate(shots):
        out = work_dir / f"{i:02d}_{shot['name']}.mp4"
        path = generate_clip(shot["prompt"], shot["duration"], out, aspect)
        if path:
            clips.append(path)
        else:
            console.print(f"[yellow]Cena '{shot['name']}' pulada.[/yellow]")
    return clips


def collect_manual_clips(clips_dir: Path) -> list[Path]:
    """Coleta clipes .mp4 de uma pasta, em ordem alfabética (modo manual)."""
    clips_dir = Path(clips_dir)
    clips = sorted(clips_dir.glob("*.mp4"))
    if not clips:
        console.print(f"[red]Nenhum .mp4 encontrado em {clips_dir}[/red]")
    else:
        console.print(f"[green]{len(clips)} clipe(s) manual(is) encontrado(s).[/green]")
    return clips
