import requests
from datetime import date, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from rich.console import Console
from automation.config import (
    YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN, YOUTUBE_CHANNEL_ID,
    TIKTOK_ACCESS_TOKEN, TIKTOK_OPEN_ID,
)

console = Console()

YOUTUBE_TOKEN_URL = "https://oauth2.googleapis.com/token"
TIKTOK_USER_INFO_URL = "https://open.tiktokapis.com/v2/user/info/"
TIKTOK_VIDEO_LIST_URL = "https://open.tiktokapis.com/v2/video/list/"


# ─────────────────────────────────────────
# YouTube Analytics
# ─────────────────────────────────────────

def _get_yt_analytics_client():
    creds = Credentials(
        token=None,
        refresh_token=YOUTUBE_REFRESH_TOKEN,
        token_uri=YOUTUBE_TOKEN_URL,
        client_id=YOUTUBE_CLIENT_ID,
        client_secret=YOUTUBE_CLIENT_SECRET,
        scopes=[
            "https://www.googleapis.com/auth/youtube.readonly",
            "https://www.googleapis.com/auth/yt-analytics.readonly",
        ],
    )
    return build("youtubeAnalytics", "v2", credentials=creds)


def get_youtube_stats(days: int = 28) -> dict:
    """Retorna métricas do canal YouTube dos últimos N dias."""
    end_date = date.today().isoformat()
    start_date = (date.today() - timedelta(days=days)).isoformat()

    try:
        client = _get_yt_analytics_client()
        response = client.reports().query(
            ids=f"channel=={YOUTUBE_CHANNEL_ID}",
            startDate=start_date,
            endDate=end_date,
            metrics="views,estimatedMinutesWatched,subscribersGained,subscribersLost,likes,comments",
            dimensions="day",
            sort="day",
        ).execute()

        rows = response.get("rows", [])
        totals = {
            "views": sum(r[1] for r in rows),
            "watch_minutes": sum(r[2] for r in rows),
            "subs_gained": sum(r[3] for r in rows),
            "subs_lost": sum(r[4] for r in rows),
            "likes": sum(r[5] for r in rows),
            "comments": sum(r[6] for r in rows),
            "net_subscribers": sum(r[3] - r[4] for r in rows),
            "daily": [{"date": r[0], "views": r[1], "subs": r[3] - r[4]} for r in rows],
            "period_days": days,
        }
        return totals

    except Exception as e:
        console.print(f"[red]Erro YouTube Analytics: {e}[/red]")
        return {}


def get_youtube_top_videos(limit: int = 10) -> list[dict]:
    """Retorna os vídeos mais vistos do canal."""
    try:
        creds = Credentials(
            token=None,
            refresh_token=YOUTUBE_REFRESH_TOKEN,
            token_uri=YOUTUBE_TOKEN_URL,
            client_id=YOUTUBE_CLIENT_ID,
            client_secret=YOUTUBE_CLIENT_SECRET,
            scopes=["https://www.googleapis.com/auth/youtube.readonly"],
        )
        youtube = build("youtube", "v3", credentials=creds)
        resp = youtube.search().list(
            part="snippet",
            channelId=YOUTUBE_CHANNEL_ID,
            order="viewCount",
            type="video",
            maxResults=limit,
        ).execute()

        video_ids = [item["id"]["videoId"] for item in resp.get("items", [])]
        if not video_ids:
            return []

        stats_resp = youtube.videos().list(
            part="snippet,statistics",
            id=",".join(video_ids),
        ).execute()

        return [
            {
                "title": item["snippet"]["title"],
                "views": int(item["statistics"].get("viewCount", 0)),
                "likes": int(item["statistics"].get("likeCount", 0)),
                "comments": int(item["statistics"].get("commentCount", 0)),
                "url": f"https://youtube.com/watch?v={item['id']}",
            }
            for item in stats_resp.get("items", [])
        ]

    except Exception as e:
        console.print(f"[red]Erro ao buscar vídeos YouTube: {e}[/red]")
        return []


# ─────────────────────────────────────────
# TikTok Analytics
# ─────────────────────────────────────────

def get_tiktok_stats() -> dict:
    """Retorna métricas do perfil TikTok."""
    headers = {"Authorization": f"Bearer {TIKTOK_ACCESS_TOKEN}"}

    try:
        resp = requests.get(
            TIKTOK_USER_INFO_URL,
            headers=headers,
            params={"fields": "display_name,follower_count,following_count,likes_count,video_count"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {}).get("user", {})
        return {
            "followers": data.get("follower_count", 0),
            "following": data.get("following_count", 0),
            "total_likes": data.get("likes_count", 0),
            "video_count": data.get("video_count", 0),
            "display_name": data.get("display_name", ""),
        }

    except Exception as e:
        console.print(f"[red]Erro TikTok profile: {e}[/red]")
        return {}


def get_tiktok_top_videos(limit: int = 10) -> list[dict]:
    """Retorna os vídeos mais recentes com métricas do TikTok."""
    headers = {"Authorization": f"Bearer {TIKTOK_ACCESS_TOKEN}"}

    try:
        resp = requests.post(
            TIKTOK_VIDEO_LIST_URL,
            headers=headers,
            json={"max_count": limit, "fields": ["id", "title", "view_count", "like_count", "comment_count", "share_count"]},
            timeout=15,
        )
        resp.raise_for_status()
        videos = resp.json().get("data", {}).get("videos", [])
        return [
            {
                "title": v.get("title", "Sem título"),
                "views": v.get("view_count", 0),
                "likes": v.get("like_count", 0),
                "comments": v.get("comment_count", 0),
                "shares": v.get("share_count", 0),
                "url": f"https://tiktok.com/@{TIKTOK_OPEN_ID}/video/{v['id']}",
            }
            for v in videos
        ]

    except Exception as e:
        console.print(f"[red]Erro TikTok vídeos: {e}[/red]")
        return []


# ─────────────────────────────────────────
# Consolidado
# ─────────────────────────────────────────

def get_all_stats(days: int = 28) -> dict:
    console.print("[cyan]Buscando analytics...[/cyan]")
    return {
        "youtube": {
            "stats": get_youtube_stats(days),
            "top_videos": get_youtube_top_videos(),
        },
        "tiktok": {
            "stats": get_tiktok_stats(),
            "top_videos": get_tiktok_top_videos(),
        },
    }
