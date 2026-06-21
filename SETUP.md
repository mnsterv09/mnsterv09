# Setup — MoneyPrinter Automation

## 1. Clonar o MoneyPrinterTurbo

```bash
git clone https://github.com/harry0703/MoneyPrinterTurbo.git
cd MoneyPrinterTurbo
cp config.example.toml config.toml
```

Edite o `config.toml` e coloque suas chaves:
- **Pexels API** → pexels.com/api (gratuita)
- **LLM** → recomendado DeepSeek ou Gemini Flash (mais baratos)

Inicie o servidor:
```bash
# Windows (one-click)
start.bat

# Docker
docker compose up

# Python manual
pip install -r requirements.txt
python main.py
```

O servidor sobe em `http://localhost:8080`

---

## 2. Configurar este projeto

```bash
# Voltar para a raiz do projeto
cd ..

# Instalar dependências
pip install -r requirements.txt

# Copiar e preencher variáveis de ambiente
cp .env.example .env
```

---

## 3. Credenciais YouTube

1. Acesse [console.cloud.google.com](https://console.cloud.google.com)
2. Crie um projeto → Ative **YouTube Data API v3** e **YouTube Analytics API**
3. Crie credenciais OAuth 2.0 (tipo: Aplicativo Desktop)
4. Baixe o `credentials.json`
5. Rode para gerar o refresh token:

```bash
python scripts/auth_youtube.py
```

Copie os valores gerados para o `.env`.

---

## 4. Credenciais TikTok

1. Acesse [developers.tiktok.com](https://developers.tiktok.com)
2. Crie um app → solicite acesso ao **Content Posting API**
3. Copie `client_key` e `client_secret` para o `.env`
4. Rode para autenticar:

```bash
python scripts/auth_tiktok.py
```

---

## 5. Uso

```bash
# Ver canais disponíveis
python run.py channels

# Gerar vídeo de um canal
python run.py generate curiosidades
python run.py generate true_crime --topic "O crime que chocou o Japão"
python run.py generate copa2026

# Gerar todos os vídeos de um canal de uma vez
python run.py batch curiosidades

# Publicar vídeo já gerado
python run.py publish caminho/video.mp4 curiosidades --title "7 fatos absurdos do Brasil"

# Pipeline completo: gera e publica automaticamente
python run.py pipeline curiosidades
python run.py pipeline true_crime --topic "Ted Bundy: a história completa"

# Analytics no terminal
python run.py analytics
python run.py analytics --days 7

# Dashboard visual no navegador
python run.py dashboard
```

---

## Estrutura de arquivos

```
├── run.py                  # CLI principal
├── requirements.txt
├── .env.example
├── automation/
│   ├── config.py           # Carrega .env e configs
│   ├── generate.py         # Integração com MoneyPrinterTurbo
│   ├── publish.py          # Publicação YouTube + TikTok
│   ├── analytics.py        # Métricas das plataformas
│   └── dashboard.py        # Dashboard Streamlit
├── configs/
│   ├── curiosidades.toml   # Config do canal Curiosidades
│   ├── true_crime.toml     # Config do canal True Crime
│   └── copa2026.toml       # Config do canal Copa 2026
└── MoneyPrinterTurbo/      # Clonar aqui
```
