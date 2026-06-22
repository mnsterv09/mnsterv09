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

  # Copa 2026 (animação anime/cartoon de gols)
  python run.py copa goal --team Brasil --opponent Argentina --scorer "Vinícius Júnior" --minute 23
  python run.py copa goal ... --clips-dir ./meus_clipes   # modo manual (sem API)
  python run.py copa from-file data/goals.json
"""
import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="MoneyPrinter Automation — geração e publicação automática de vídeos")
copa_app = typer.Typer(help="Pipeline de animação de gols da Copa 2026")
app.add_typer(copa_app, name="copa")
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


# ─────────────────────────────────────────
# Copa 2026 — animação de gols
# ─────────────────────────────────────────

@copa_app.command("goal")
def copa_goal(
    team: str = typer.Option(..., "--team", help="Seleção que marcou (ex: Brasil)"),
    opponent: str = typer.Option(..., "--opponent", help="Adversário"),
    scorer: str = typer.Option(..., "--scorer", help="Nome do jogador"),
    minute: int = typer.Option(..., "--minute", help="Minuto do gol"),
    number: int = typer.Option(10, "--number", help="Número da camisa"),
    play_type: str = typer.Option("chute de fora da área", "--play", help="Tipo de jogada"),
    stage: str = typer.Option("Fase de Grupos", "--stage", help="Fase da Copa"),
    score: str = typer.Option("", "--score", help="Placar após o gol (ex: '2 a 1')"),
    clips_dir: Path = typer.Option(None, "--clips-dir", help="Pasta com clipes manuais (.mp4). Sem isso, gera via IA."),
    music: Path = typer.Option(None, "--music", help="Trilha de fundo .mp3 (opcional)"),
    publish: bool = typer.Option(False, "--publish", help="Publicar no YouTube + TikTok ao final"),
):
    """Produz a animação de um gol a partir dos dados informados."""
    from automation.copa.goals import Goal
    from automation.copa.pipeline import make_goal_video, title_for

    goal = Goal(
        team=team, opponent=opponent, scorer=scorer, minute=minute,
        number=number, play_type=play_type, stage=stage, score_after=score,
    )
    video = make_goal_video(goal, clips_dir=clips_dir, music=music)
    if not video:
        raise typer.Exit(1)

    console.print(f"[bold green]Pronto: {video}[/bold green]")

    if publish:
        from automation.publish import publish_all
        results = publish_all(video, title_for(goal), "copa2026")
        console.print(results)


@copa_app.command("from-file")
def copa_from_file(
    file: Path = typer.Argument(..., help="JSON com a lista de gols"),
    clips_root: Path = typer.Option(None, "--clips-root", help="Pasta raiz; cada gol busca clipes em <root>/<slug>"),
    music: Path = typer.Option(None, "--music", help="Trilha de fundo .mp3 (opcional)"),
    publish: bool = typer.Option(False, "--publish", help="Publicar cada vídeo ao final"),
):
    """Produz vídeos para todos os gols de um arquivo JSON."""
    from automation.copa.goals import load_goals
    from automation.copa.pipeline import make_goal_video, title_for

    if not file.exists():
        console.print(f"[red]Arquivo não encontrado: {file}[/red]")
        raise typer.Exit(1)

    goals = load_goals(file)
    console.print(f"[cyan]{len(goals)} gol(is) carregado(s).[/cyan]")

    produced = []
    for goal in goals:
        clips_dir = (clips_root / goal.slug) if clips_root else None
        video = make_goal_video(goal, clips_dir=clips_dir, music=music)
        if video:
            produced.append((goal, video))
            if publish:
                from automation.publish import publish_all
                publish_all(video, title_for(goal), "copa2026")

    console.print(f"[bold green]{len(produced)}/{len(goals)} vídeos produzidos.[/bold green]")


if __name__ == "__main__":
    app()
