"""
Gera o TIKTOK_ACCESS_TOKEN para colocar no .env
Execute uma única vez após criar o app no TikTok for Developers.
"""
import os
import secrets
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8091/callback"

SCOPES = "video.upload,video.list,user.info.basic"
AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"

if not CLIENT_KEY:
    print("Erro: TIKTOK_CLIENT_KEY não encontrado no .env")
    exit(1)

code_verifier = secrets.token_urlsafe(64)
state = secrets.token_urlsafe(16)

auth_params = {
    "client_key": CLIENT_KEY,
    "response_type": "code",
    "scope": SCOPES,
    "redirect_uri": REDIRECT_URI,
    "state": state,
}

auth_link = AUTH_URL + "?" + urllib.parse.urlencode(auth_params)
print(f"\nAbrindo navegador para autenticação TikTok...")
webbrowser.open(auth_link)

auth_code = None


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        auth_code = params.get("code", [None])[0]
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Autenticacao concluida! Pode fechar esta aba.")

    def log_message(self, format, *args):
        pass


server = HTTPServer(("localhost", 8091), CallbackHandler)
server.handle_request()

if not auth_code:
    print("Erro: código de autenticação não recebido.")
    exit(1)

resp = requests.post(TOKEN_URL, data={
    "client_key": CLIENT_KEY,
    "client_secret": CLIENT_SECRET,
    "code": auth_code,
    "grant_type": "authorization_code",
    "redirect_uri": REDIRECT_URI,
})

data = resp.json()

if "access_token" not in data:
    print(f"Erro ao obter token: {data}")
    exit(1)

print("\n=== Coloque isso no seu .env ===")
print(f"TIKTOK_ACCESS_TOKEN={data['access_token']}")
print(f"TIKTOK_OPEN_ID={data.get('open_id', '')}")
print("================================\n")
