"""Clasificacion global: suma de puntos de cada equipo en todos los torneos finalizados."""
from __future__ import annotations
from .models import Tournament, Team


def compute_global_ranking(tournaments: list[Tournament], teams: list[Team]) -> list[dict]:
    team_names = {t.id: (t.name, t.tag) for t in teams}
    totals: dict[str, dict] = {}

    for t in tournaments:
        if t.status != "finished":
            continue
        for entry in t.final_standings:
            tid = entry["team_id"]
            if tid not in totals:
                name, tag = team_names.get(tid, (tid, ""))
                totals[tid] = {"team_id": tid, "name": name, "tag": tag, "points": 0.0,
                                "tournaments": 0, "history": []}
            totals[tid]["points"] += entry["points"]
            totals[tid]["tournaments"] += 1
            pos_label = f"{entry['position_from']}" if entry["position_from"] == entry["position_to"] \
                else f"{entry['position_from']}-{entry['position_to']}"
            totals[tid]["history"].append({
                "tournament": t.name, "position": pos_label, "points": entry["points"],
            })

    ranking = sorted(totals.values(), key=lambda r: -r["points"])
    for i, r in enumerate(ranking, start=1):
        r["rank"] = i
        r["points"] = round(r["points"], 1)
    return ranking
