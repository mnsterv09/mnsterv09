"""
Modelo de dados de um gol e carregamento a partir de JSON.

Um gol pode vir de:
  - entrada manual (CLI ou JSON) — o caminho rápido durante os jogos
  - um arquivo data/goals.json com vários gols para gerar em lote
"""
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Goal:
    team: str                      # ex: "Brasil"
    opponent: str                  # ex: "Argentina"
    scorer: str                    # ex: "Vinícius Júnior"
    minute: int                    # ex: 23
    number: int = 10               # número da camisa
    stage: str = "Fase de Grupos"  # ex: "Oitavas de Final"
    play_type: str = "chute de fora da área"  # tipo da jogada
    description: str = ""          # detalhe livre opcional
    score_after: str = ""          # ex: "2 a 1" (placar após o gol)
    slug: str = ""                 # id curto para nome de arquivo

    def __post_init__(self):
        if not self.slug:
            base = f"{self.team}-{self.scorer}-{self.minute}min"
            self.slug = (
                base.lower()
                .replace(" ", "-")
                .replace("í", "i").replace("ú", "u").replace("á", "a")
                .replace("ã", "a").replace("é", "e").replace("ó", "o").replace("ç", "c")
            )

    @property
    def match(self) -> str:
        return f"{self.team} x {self.opponent}"


def load_goals(path: str | Path) -> list[Goal]:
    """Carrega uma lista de gols de um arquivo JSON."""
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("goals", [])
    return [Goal(**item) for item in data]
