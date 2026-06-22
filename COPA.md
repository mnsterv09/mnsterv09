# Canal Copa 2026 — Animação de Gols (Anime/Cartoon)

Pipeline que transforma um gol da Copa em um Short animado estilo anime, com
narração, legendas e trilha — pronto para YouTube Shorts e TikTok.

## Fluxo

```
Dados do gol
     ↓
Prompts de cena (build-up / finalização / comemoração)  +  roteiro de narração
     ↓
Animação IA (fal.ai → Kling/Runway)   OU   clipes feitos por você na web
     ↓
Narração + legendas sincronizadas (Edge TTS, grátis)
     ↓
ffmpeg: normaliza → concatena → mixa áudio → queima legenda
     ↓
Vídeo 9:16 final
```

## Pré-requisitos

```bash
pip install -r requirements.txt    # inclui edge-tts e fal-client
# ffmpeg é dependência de sistema:
#   Windows: winget install Gyan.FFmpeg   |   Mac: brew install ffmpeg
#   Linux:   sudo apt install ffmpeg
```

Para o modo IA, coloque sua chave do [fal.ai](https://fal.ai/dashboard/keys) no `.env`:
```
FAL_KEY=...
```

## Dois modos de produção

### Modo IA (automático)
A pipeline gera as 3 cenas via fal.ai. Custo aproximado: alguns centavos a poucos dólares por vídeo, dependendo do modelo.

```bash
python run.py copa goal \
  --team Brasil --opponent Argentina \
  --scorer "Vinícius Júnior" --minute 23 \
  --number 7 --play drible --score "1 a 0"
```

### Modo manual (sem custo de API)
Você gera os clipes na interface web do Kling/Runway, salva os `.mp4` numa pasta
(em ordem alfabética = ordem das cenas) e a pipeline cuida do resto:

```bash
python run.py copa goal \
  --team Brasil --opponent Argentina --scorer "Vinícius Júnior" --minute 23 \
  --clips-dir ./meus_clipes
```

## Produção em lote

Edite `data/goals.json` (use `data/goals.example.json` como base) e rode:

```bash
python run.py copa from-file data/goals.json
# modo manual em lote: cada gol procura clipes em <root>/<slug>
python run.py copa from-file data/goals.json --clips-root ./clipes
```

## Publicar direto

Adicione `--publish` para subir no YouTube Shorts + TikTok ao final
(precisa das credenciais do `SETUP.md` configuradas):

```bash
python run.py copa goal --team Brasil --opponent Espanha \
  --scorer Rodrygo --minute 89 --play "chute de fora da área" --publish
```

## Tipos de jogada disponíveis (`--play`)

`chute de fora da área` · `cabeçada` · `pênalti` · `contra-ataque` ·
`drible` · `voleio` · `falta` · `chapéu`

Cada um gera uma animação de finalização diferente. Qualquer outro valor usa
uma finalização genérica.

## Dica de velocidade (aproveitar o hype)

Durante os jogos, o gargalo é o tempo. Recomendado:
1. Deixe os clipes-base de comemoração/torcida prontos com antecedência.
2. No gol, gere só a cena da finalização (a mais específica) e reaproveite as outras.
3. Publique em até 1-2h após o gol, enquanto o termo está em alta nas buscas.
