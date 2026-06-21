#!/usr/bin/env python3
"""
MoneyPrinter Automation — CLI principal
Uso:
  python run.py generate <canal> [--topic "Tópico do vídeo"]
  python run.py batch <canal>
  python run.py publish <video.mp4> <canal> --title "Título"
  python run.py pipeline <canal> [--topic "Tópico"]
  python run.py analytics [--days 28]
  python run.py dashboard
  python run.py channels
"""
import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="MoneyPrinter Automation — geração e publicação automática de vídeos")
console = Console()


@app.command()
def channels():
    """Lista os canais configurados."""
    from automation.config import list_channels, load_channel_config
    table = Table(title="Canais Configurados", show_header=True, header_style="bold cyan")
    table.add_column("Canal")
    table.add_column("Voz")
    table.add_column("Formato")
    table.add_column("Tópicos")

    for ch in list_channels():
        cfg = load_channel_config(ch)
        table.add_row(
            ch,
            cfg["video"]["voice"],
            cfg["video"]["aspect"],
            str(len(cfg["topics"]["list"])),
        )
    console.print(table)


@app.command()
def generate(
    canal: str = typer.Argument(..., help="Nome do canal (curiosidades, true_crime, copa2026)"),
    topic: str = typer.Option(None, "--topic", "-t", help="Tópico específico do vídeo"),
):
    """Gera um vídeo via MoneyPrinterTurbo."""
    from automation.generate import generate_video
    path = generate_video(canal, topic)
    if path:
        console.print(f"[bold green]Vídeo gerado: {path}[/bold green]")
    else:
        console.print("[red]Falha na geração do vídeo.[/red]")
        raise typer.Exit(1)


@app.command()
def batch(
    canal: str = typer.Argument(..., help="Nome do canal"),
):
    """Gera todos os vídeos da lista de tópicos do canal."""
    from automation.generate import batch_generate
    paths = batch_generate(canal)
    console.print(f"[bold green]{len(paths)} vídeos gerados.[/bold green]")


@app.command()
def publish(
    video: Path = typer.Argument(..., help="Caminho do vídeo .mp4"),
    canal: str = typer.Argument(..., help="Nome do canal"),
    title: str = typer.Option(..., "--title", "-t", help="Título do vídeo"),
):
    """Publica um vídeo no YouTube Shorts e TikTok."""
    from automation.publish import publish_all
    if not video.exists():
        console.print(f"[red]Arquivo não encontrado: {video}[/red]")
        raise typer.Exit(1)
    results = publish_all(video, title, canal)
    console.print(results)


@app.command()
def pipeline(
    canal: str = typer.Argument(..., help="Nome do canal"),
    topic: str = typer.Option(None, "--topic", "-t", help="Tópico do vídeo"),
):
    """Gera e publica automaticamente em sequência."""
    from automation.generate import generate_video
    from automation.publish import publish_all

    console.print(f"[bold cyan]Pipeline iniciado para canal: {canal}[/bold cyan]")

    video_path = generate_video(canal, topic)
    if not video_path:
        console.print("[red]Pipeline abortado: falha na geração.[/red]")
        raise typer.Exit(1)

    title = topic or video_path.stem
    results = publish_all(video_path, title, canal)

    console.print("\n[bold green]Pipeline concluído![/bold green]")
    for platform, url in results.items():
        status = f"[green]{url}[/green]" if url else "[red]Falhou[/red]"
        console.print(f"  {platform}: {status}")


@app.command()
def analytics(
    days: int = typer.Option(28, "--days", "-d", help="Número de dias para análise"),
):
    """Exibe analytics consolidado de YouTube e TikTok no terminal."""
    from automation.analytics import get_youtube_stats, get_tiktok_stats, get_youtube_top_videos, get_tiktok_top_videos

    yt = get_youtube_stats(days)
    tt = get_tiktok_stats()

    table = Table(title=f"Analytics — Últimos {days} dias", show_header=True, header_style="bold cyan")
    table.add_column("Métrica")
    table.add_column("YouTube", justify="right", style="red")
    table.add_column("TikTok", justify="right", style="cyan")

    table.add_row("Views", f"{yt.get('views', 0):,}", "—")
    table.add_row("Inscritos / Seguidores", f"+{yt.get('net_subscribers', 0):,}", f"{tt.get('followers', 0):,}")
    table.add_row("Likes", f"{yt.get('likes', 0):,}", f"{tt.get('total_likes', 0):,}")
    table.add_row("Comentários", f"{yt.get('comments', 0):,}", "—")
    table.add_row("Minutos assistidos", f"{yt.get('watch_minutes', 0):,}", "—")
    table.add_row("Total de vídeos", "—", f"{tt.get('video_count', 0):,}")
    console.print(table)

    console.print("\n[bold]Top 5 YouTube:[/bold]")
    for i, v in enumerate(get_youtube_top_videos(5), 1):
        console.print(f"  {i}. {v['title'][:60]} — [red]{v['views']:,} views[/red]")

    console.print("\n[bold]Top 5 TikTok:[/bold]")
    for i, v in enumerate(get_tiktok_top_videos(5), 1):
        console.print(f"  {i}. {v['title'][:60]} — [cyan]{v['views']:,} views[/cyan]")


@app.command()
def dashboard():
    """Abre o dashboard visual no navegador."""
    import subprocess, sys
    console.print("[cyan]Abrindo dashboard em http://localhost:8501[/cyan]")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "automation/dashboard.py"])


if __name__ == "__main__":
    app()
