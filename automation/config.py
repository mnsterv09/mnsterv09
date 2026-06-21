import os
import tomli
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

MPT_API_URL = os.getenv("MPT_API_URL", "http://localhost:8080")
MPT_OUTPUT_DIR = Path(os.getenv("MPT_OUTPUT_DIR", BASE_DIR / "MoneyPrinterTurbo/storage/cache/videos"))

YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")
YOUTUBE_REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")

TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN")
TIKTOK_OPEN_ID = os.getenv("TIKTOK_OPEN_ID")

CONFIGS_DIR = BASE_DIR / "configs"


def load_channel_config(channel: str) -> dict:
    path = CONFIGS_DIR / f"{channel}.toml"
    if not path.exists():
        raise FileNotFoundError(f"Config não encontrado: {path}")
    with open(path, "rb") as f:
        return tomli.load(f)


def list_channels() -> list[str]:
    return [p.stem for p in CONFIGS_DIR.glob("*.toml")]
