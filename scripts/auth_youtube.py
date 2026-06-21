"""
Gera o YOUTUBE_REFRESH_TOKEN para colocar no .env
Execute uma única vez após criar as credenciais no Google Cloud Console.
"""
import json
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

CLIENT_CONFIG = {
    "installed": {
        "client_id": os.getenv("YOUTUBE_CLIENT_ID"),
        "client_secret": os.getenv("YOUTUBE_CLIENT_SECRET"),
        "redirect_uris": ["http://localhost"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

if not CLIENT_CONFIG["installed"]["client_id"]:
    print("Erro: YOUTUBE_CLIENT_ID não encontrado no .env")
    exit(1)

flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, SCOPES)
creds = flow.run_local_server(port=8090)

print("\n=== Coloque isso no seu .env ===")
print(f"YOUTUBE_REFRESH_TOKEN={creds.refresh_token}")
print("================================\n")
