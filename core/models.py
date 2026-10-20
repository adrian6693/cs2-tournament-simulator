"""Modelos de datos del dominio. Todo serializable a/desde dict para guardarlo en JSON."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional
import uuid


def new_id() -> str:
    return uuid.uuid4().hex[:10]


@dataclass
class Team:
    id: str
    name: str
    tag: str = ""

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d):
        return Team(id=d["id"], name=d["name"], tag=d.get("tag", ""))


@dataclass
class Match:
    id: str
    round: int                 # numero de ronda dentro de la etapa (1, 2, 3...)
    slot: int                  # posicion dentro de la ronda (para ordenar el bracket)
    team1_id: Optional[str] = None
    team2_id: Optional[str] = None
    score1: int = 0
    score2: int = 0
    bo: int = 1                 # al mejor de N mapas
    winner_id: Optional[str] = None
    bye: bool = False           # True si es un pase directo (sin rival)
    played: bool = False
    group: Optional[str] = None  # etiqueta de grupo ("A", "B"...) para round robin por grupos
    # para bracket de eliminacion: de donde vienen los equipos (para pintar lineas)
    from_match1: Optional[str] = None
    from_match2: Optional[str] = None

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d):
        m = Match(id=d["id"], round=d["round"], slot=d["slot"])
        m.__dict__.update(d)
        return m


@dataclass
class PointsRange:
    pos_from: int
    pos_to: int
    points: int

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d):
        return PointsRange(d["pos_from"], d["pos_to"], d["points"])


@dataclass
class Stage:
    id: str
    name: str
    type: str                   # "round_robin" | "single_elim" | "swiss"
    config: dict = field(default_factory=dict)
    participants: list = field(default_factory=list)   # lista de team_id, en orden de seed
    matches: list = field(default_factory=list)         # lista de Match
    standings: list = field(default_factory=list)       # lista de dict {team_id, position, ...}
    finished: bool = False

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "type": self.type,
            "config": self.config, "participants": self.participants,
            "matches": [m.to_dict() for m in self.matches],
            "standings": self.standings, "finished": self.finished,
        }

    @staticmethod
    def from_dict(d):
        s = Stage(id=d["id"], name=d["name"], type=d["type"], config=d.get("config", {}),
                   participants=d.get("participants", []), finished=d.get("finished", False))
        s.matches = [Match.from_dict(m) for m in d.get("matches", [])]
        s.standings = d.get("standings", [])
        return s


@dataclass
class Tournament:
    id: str
    name: str
    date: str = ""
    importance: float = 1.0       # multiplicador de puntos (importancia del torneo)
    importance_label: str = "Regional"
    status: str = "setup"          # setup | in_progress | finished
    teams: list = field(default_factory=list)     # lista de Team
    points_table: list = field(default_factory=list)  # lista de PointsRange
    stages: list = field(default_factory=list)     # lista de Stage
    final_standings: list = field(default_factory=list)  # [{team_id, position, points}]
    trophy_image: str = ""         # nombre de fichero dentro de data/trophies/ (opcional)

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "date": self.date,
            "importance": self.importance, "importance_label": self.importance_label,
            "status": self.status,
            "teams": [t.to_dict() for t in self.teams],
            "points_table": [p.to_dict() for p in self.points_table],
            "stages": [s.to_dict() for s in self.stages],
            "final_standings": self.final_standings,
            "trophy_image": self.trophy_image,
        }

    @staticmethod
    def from_dict(d):
        t = Tournament(id=d["id"], name=d["name"], date=d.get("date", ""),
                        importance=d.get("importance", 1.0),
                        importance_label=d.get("importance_label", "Regional"),
                        status=d.get("status", "setup"),
                        trophy_image=d.get("trophy_image", ""))
        t.teams = [Team.from_dict(x) for x in d.get("teams", [])]
        t.points_table = [PointsRange.from_dict(x) for x in d.get("points_table", [])]
        t.stages = [Stage.from_dict(x) for x in d.get("stages", [])]
        t.final_standings = d.get("final_standings", [])
        return t
