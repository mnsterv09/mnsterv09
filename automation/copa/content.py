"""
Geração do conteúdo textual a partir de um gol:
  - prompts visuais por cena (para o modelo de vídeo IA)
  - roteiro de narração (para o TTS)

A animação é dividida em 3 cenas curtas (build-up, finalização, comemoração)
porque modelos text-to-video geram clipes de 5s com mais coerência do que
uma única cena longa.
"""
from automation.copa.goals import Goal

# Cores/uniformes por seleção — usados no prompt para manter consistência visual.
TEAM_VISUALS: dict[str, str] = {
    "Brasil": "yellow jersey with green trim, blue shorts",
    "Argentina": "light blue and white striped jersey, black shorts",
    "França": "blue jersey, white shorts",
    "France": "blue jersey, white shorts",
    "Inglaterra": "white jersey, navy shorts",
    "England": "white jersey, navy shorts",
    "Portugal": "dark red jersey, green trim, green shorts",
    "Espanha": "red jersey, navy shorts",
    "Spain": "red jersey, navy shorts",
    "Alemanha": "white jersey with black details, black shorts",
    "Germany": "white jersey with black details, black shorts",
    "Holanda": "bright orange jersey, black shorts",
    "Países Baixos": "bright orange jersey, black shorts",
    "Estados Unidos": "white jersey with red and blue, navy shorts",
    "México": "green jersey, white shorts",
    "Croácia": "red and white checkered jersey, blue shorts",
    "Uruguai": "sky blue jersey, black shorts",
}

DEFAULT_KIT = "team colored jersey and shorts"

# Como cada tipo de jogada deve ser animado na cena da finalização.
PLAY_VISUALS: dict[str, str] = {
    "chute de fora da área": "strikes a powerful long-range shot from outside the box, ball curving into the top corner",
    "cabeçada": "leaps high and powerfully heads the ball, sending it into the net",
    "pênalti": "calmly steps up and converts a penalty kick, sending the keeper the wrong way",
    "contra-ataque": "sprints on a fast counter-attack and slots the ball past the keeper",
    "drible": "dribbles past two defenders with quick footwork and finishes into the net",
    "voleio": "connects with a spectacular mid-air volley that flies into the goal",
    "falta": "curls a free kick over the wall into the top corner",
    "chapéu": "lifts the ball over the goalkeeper with a delicate chip into the empty net",
}

DEFAULT_PLAY = "finishes with a precise shot into the corner of the net"

STYLE = (
    "Studio Ghibli inspired anime aesthetic, vibrant saturated colors, "
    "dynamic motion lines, dramatic cinematic lighting, fluid smooth animation, "
    "stadium packed with cheering fans, 4K quality, sports anime style"
)


def _kit(team: str) -> str:
    return TEAM_VISUALS.get(team, DEFAULT_KIT)


def _play(play_type: str) -> str:
    return PLAY_VISUALS.get(play_type.lower().strip(), DEFAULT_PLAY)


def build_shot_prompts(goal: Goal) -> list[dict]:
    """Retorna a lista de cenas (nome, prompt, duração em s) para a animação."""
    kit = _kit(goal.team)
    action = _play(goal.play_type)
    player = f"soccer player wearing {kit}, number {goal.number}"

    return [
        {
            "name": "buildup",
            "duration": 5,
            "prompt": (
                f"Anime-style soccer scene. A {player} receives the ball in midfield "
                f"and accelerates toward the goal, defenders chasing. Sense of speed and tension. "
                f"{STYLE}."
            ),
        },
        {
            "name": "goal",
            "duration": 5,
            "prompt": (
                f"Anime-style soccer scene. The {player} {action}. The goalkeeper dives but "
                f"cannot reach the ball. The net ripples. Explosive impact moment. "
                f"{STYLE}."
            ),
        },
        {
            "name": "celebration",
            "duration": 5,
            "prompt": (
                f"Anime-style soccer scene. The {player} celebrates with arms wide open, "
                f"sliding on his knees, teammates running to embrace him, the crowd erupting "
                f"in confetti and flags. Pure euphoria. {STYLE}."
            ),
        },
    ]


def build_narration(goal: Goal) -> str:
    """Roteiro curto e energético para a narração TTS."""
    placar = f" {goal.score_after}!" if goal.score_after else "!"
    return (
        f"{goal.minute} minutos. {goal.match}. "
        f"A bola chega para {goal.scorer}. "
        f"Ele avança... e finaliza! "
        f"GOOOOL DO {goal.team.upper()}!{placar} "
        f"Um gol que entra para a história da Copa do Mundo 2026. "
        f"Segue o canal pra ver a animação de cada gol do torneio."
    )


def build_title(goal: Goal) -> str:
    """Título para publicação."""
    return f"{goal.scorer} | Gol do {goal.team} aos {goal.minute}min — Copa 2026 (Anime)"
