import os
import time
import requests
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from rich.console import Console
from automation.config import (
    YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN,
    TIKTOK_ACCESS_TOKEN, TIKTOK_OPEN_ID,
    load_channel_config,
)

console = Console()

YOUTUBE_TOKEN_URL = "https://oauth2.googleapis.com/token"
TIKTOK_UPLOAD_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"
TIKTOK_STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"


# ─────────────────────────────────────────
# YouTube
# ─────────────────────────────────────────

def _get_youtube_client():
    creds = Credentials(
        token=None,
        refresh_token=YOUTUBE_REFRESH_TOKEN,
        token_uri=YOUTUBE_TOKEN_URL,
        client_id=YOUTUBE_CLIENT_ID,
        client_secret=YOUTUBE_CLIENT_SECRET,
        scopes=["https://www.googleapis.com/auth/youtube.upload",
                "https://www.googleapis.com/auth/youtube.readonly"],
    )
    return build("youtube", "v3", credentials=creds)


def publish_youtube(video_path: Path, title: str, channel: str) -> str | None:
    """Faz upload do vídeo no YouTube como Short. Retorna o video_id."""
    cfg = load_channel_config(channel)
    hashtags = " ".join(cfg["channel"]["youtube_hashtags"])
    playlist_id = cfg["channel"].get("youtube_playlist_id")

    description = f"{hashtags}\n\nSiga para mais conteúdo diário!"
    tags = [h.replace("#", "") for h in cfg["channel"]["youtube_hashtags"]]

    body = {
        "snippet": {
            "title": f"{title} #Shorts",
            "description": description,
            "tags": tags,
            "categoryId": "22",
            "defaultLanguage": "pt",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(str(video_path), mimetype="video/mp4", resumable=True, chunksize=1024 * 1024 * 5)

    try:
        youtube = _get_youtube_client()
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                console.print(f"[dim]YouTube upload: {int(status.progress() * 100)}%[/dim]")

        video_id = response["id"]
        console.print(f"[green]YouTube publicado: https://youtube.com/shorts/{video_id}[/green]")

        if playlist_id:
            youtube.playlistItems().insert(
                part="snippet",
                body={"snippet": {"playlistId": playlist_id, "resourceId": {"kind": "youtube#video", "videoId": video_id}}}
            ).execute()

        return video_id

    except Exception as e:
        console.print(f"[red]Erro no YouTube: {e}[/red]")
        return None


# ─────────────────────────────────────────
# TikTok
# ─────────────────────────────────────────

def publish_tiktok(video_path: Path, title: str, channel: str) -> str | None:
    """Faz upload do vídeo no TikTok. Retorna o publish_id."""
    cfg = load_channel_config(channel)
    hashtags = " ".join([f"#{h}" for h in cfg["channel"]["tiktok_hashtags"]])
    caption = f"{title} {hashtags}"

    file_size = os.path.getsize(video_path)
    headers = {
        "Authorization": f"Bearer {TIKTOK_ACCESS_TOKEN}",
        "Content-Type": "application/json; charset=UTF-8",
    }

    # Etapa 1: inicializar upload
    init_payload = {
        "post_info": {
            "title": caption[:150],
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": file_size,
            "chunk_size": file_size,
            "total_chunk_count": 1,
        },
    }

    try:
        resp = requests.post(TIKTOK_UPLOAD_URL, json=init_payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()["data"]
        upload_url = data["upload_url"]
        publish_id = data["publish_id"]

        # Etapa 2: upload do arquivo
        with open(video_path, "rb") as f:
            video_bytes = f.read()

        upload_headers = {
            "Content-Type": "video/mp4",
            "Content-Range": f"bytes 0-{file_size - 1}/{file_size}",
            "Content-Length": str(file_size),
        }
        upload_resp = requests.put(upload_url, data=video_bytes, headers=upload_headers, timeout=120)
        upload_resp.raise_for_status()

        # Etapa 3: aguardar processamento
        _wait_tiktok_publish(publish_id, headers)
        console.print(f"[green]TikTok publicado! publish_id: {publish_id}[/green]")
        return publish_id

    except Exception as e:
        console.print(f"[red]Erro no TikTok: {e}[/red]")
        return None


def _wait_tiktok_publish(publish_id: str, headers: dict, timeout: int = 120) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = requests.post(
                TIKTOK_STATUS_URL,
                json={"publish_id": publish_id},
                headers=headers,
                timeout=15,
            )
            status = resp.json().get("data", {}).get("status")
            if status == "PUBLISH_COMPLETE":
                return True
            if status in ("FAILED", "PUBLISH_FAILED"):
                console.print(f"[red]TikTok falhou: {status}[/red]")
                return False
            time.sleep(5)
        except Exception:
            time.sleep(5)
    return False


# ─────────────────────────────────────────
# Publicação em todas as plataformas
# ─────────────────────────────────────────

def publish_all(video_path: Path, title: str, channel: str) -> dict:
    """Publica o vídeo no YouTube e TikTok. Retorna IDs de cada plataforma."""
    console.print(f"\n[bold cyan]Publicando: {title}[/bold cyan]")
    results = {}

    yt_id = publish_youtube(video_path, title, channel)
    results["youtube"] = f"https://youtube.com/shorts/{yt_id}" if yt_id else None

    tt_id = publish_tiktok(video_path, title, channel)
    results["tiktok"] = tt_id

    return results
