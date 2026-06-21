import time
import requests
from pathlib import Path
from rich.console import Console
from automation.config import MPT_API_URL, MPT_OUTPUT_DIR, load_channel_config

console = Console()


def generate_video(channel: str, topic: str | None = None) -> Path | None:
    """
    Chama a API do MoneyPrinterTurbo para gerar um vídeo.
    Retorna o caminho do vídeo gerado.
    """
    cfg = load_channel_config(channel)
    video_cfg = cfg["video"]
    subtitle_cfg = cfg["subtitles"]
    audio_cfg = cfg["audio"]

    if topic is None:
        topics = cfg["topics"]["list"]
        topic = topics[0]
        console.print(f"[yellow]Tópico não informado. Usando: {topic}[/yellow]")

    payload = {
        "video_subject": topic,
        "video_language": video_cfg["language"],
        "voice_name": video_cfg["voice"],
        "video_aspect": video_cfg["aspect"],
        "video_clip_duration": video_cfg["clip_duration"],
        "video_count": video_cfg["count"],
        "subtitle_enabled": subtitle_cfg["enabled"],
        "font_name": subtitle_cfg["font"],
        "font_size": subtitle_cfg["font_size"],
        "text_fore_color": subtitle_cfg["color"],
        "stroke_color": subtitle_cfg["stroke_color"],
        "stroke_width": subtitle_cfg["stroke_width"],
        "subtitle_position": subtitle_cfg["position"],
        "background_music_volume": audio_cfg["background_music_volume"],
    }

    console.print(f"[cyan]Gerando vídeo: [bold]{topic}[/bold][/cyan]")

    try:
        resp = requests.post(f"{MPT_API_URL}/api/v1/videos", json=payload, timeout=10)
        resp.raise_for_status()
        task_id = resp.json().get("task_id")
        console.print(f"[green]Task iniciada: {task_id}[/green]")
        return _wait_for_video(task_id)
    except requests.exceptions.ConnectionError:
        console.print("[red]Erro: MoneyPrinterTurbo não está rodando. Execute-o primeiro.[/red]")
        return None
    except Exception as e:
        console.print(f"[red]Erro ao gerar vídeo: {e}[/red]")
        return None


def _wait_for_video(task_id: str, timeout: int = 600, interval: int = 5) -> Path | None:
    """Aguarda o vídeo ficar pronto e retorna o caminho do arquivo."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = requests.get(f"{MPT_API_URL}/api/v1/tasks/{task_id}", timeout=10)
            data = resp.json()
            status = data.get("state")

            if status == "complete":
                video_path = data.get("video_path") or _find_latest_video()
                if video_path:
                    console.print(f"[green]Vídeo pronto: {video_path}[/green]")
                    return Path(video_path)

            elif status == "failed":
                console.print(f"[red]Geração falhou: {data.get('message')}[/red]")
                return None

            console.print(f"[dim]Aguardando... status: {status}[/dim]")
            time.sleep(interval)

        except Exception as e:
            console.print(f"[yellow]Checando status... ({e})[/yellow]")
            time.sleep(interval)

    console.print("[red]Timeout: vídeo não foi gerado no tempo esperado.[/red]")
    return None


def _find_latest_video() -> Path | None:
    """Fallback: busca o vídeo mais recente na pasta de output do MPT."""
    videos = sorted(MPT_OUTPUT_DIR.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    return videos[0] if videos else None


def batch_generate(channel: str) -> list[Path]:
    """Gera todos os vídeos da lista de tópicos do canal."""
    cfg = load_channel_config(channel)
    topics = cfg["topics"]["list"]
    results = []

    for topic in topics:
        path = generate_video(channel, topic)
        if path:
            results.append(path)

    console.print(f"[bold green]{len(results)}/{len(topics)} vídeos gerados com sucesso.[/bold green]")
    return results
