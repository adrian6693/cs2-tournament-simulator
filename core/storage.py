"""Persistencia sencilla en ficheros JSON."""
from __future__ import annotations
import json
import os
import shutil
import uuid
from .models import Team, Tournament

BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
TOURNAMENTS_DIR = os.path.join(BASE_DIR, "tournaments")
TEAMS_FILE = os.path.join(BASE_DIR, "teams.json")
TROPHIES_DIR = os.path.join(BASE_DIR, "trophies")


def ensure_dirs():
    os.makedirs(TOURNAMENTS_DIR, exist_ok=True)
    os.makedirs(TROPHIES_DIR, exist_ok=True)


# ---------- Equipos (roster global) ----------

def load_teams() -> list[Team]:
    ensure_dirs()
    if not os.path.exists(TEAMS_FILE):
        return []
    with open(TEAMS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Team.from_dict(t) for t in data.get("teams", [])]


def save_teams(teams: list[Team]):
    ensure_dirs()
    with open(TEAMS_FILE, "w", encoding="utf-8") as f:
        json.dump({"teams": [t.to_dict() for t in teams]}, f, indent=2, ensure_ascii=False)


# ---------- Torneos ----------

def _tournament_path(tournament_id: str) -> str:
    return os.path.join(TOURNAMENTS_DIR, f"{tournament_id}.json")


def list_tournament_ids() -> list[str]:
    ensure_dirs()
    return [f[:-5] for f in os.listdir(TOURNAMENTS_DIR) if f.endswith(".json")]


def load_tournament(tournament_id: str) -> Tournament:
    with open(_tournament_path(tournament_id), "r", encoding="utf-8") as f:
        data = json.load(f)
    return Tournament.from_dict(data)


def load_all_tournaments() -> list[Tournament]:
    return [load_tournament(tid) for tid in list_tournament_ids()]


def save_tournament(t: Tournament):
    ensure_dirs()
    with open(_tournament_path(t.id), "w", encoding="utf-8") as f:
        json.dump(t.to_dict(), f, indent=2, ensure_ascii=False)


def delete_tournament(tournament_id: str):
    path = _tournament_path(tournament_id)
    if os.path.exists(path):
        os.remove(path)


# ---------- Trofeos (imagen personalizada por torneo) ----------

def copy_trophy_image(source_path: str, tournament_id: str) -> str:
    """Copia la imagen elegida a data/trophies/ y devuelve el nombre de fichero guardado."""
    ensure_dirs()
    ext = os.path.splitext(source_path)[1] or ".png"
    filename = f"{tournament_id}_{uuid.uuid4().hex[:6]}{ext}"
    dest = os.path.join(TROPHIES_DIR, filename)
    shutil.copyfile(source_path, dest)
    return filename


def trophy_image_path(filename: str) -> str | None:
    if not filename:
        return None
    path = os.path.join(TROPHIES_DIR, filename)
    return path if os.path.exists(path) else None
