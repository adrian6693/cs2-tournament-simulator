"""Estadisticas agregadas de un equipo a partir de todos sus torneos."""
from __future__ import annotations
from .models import Tournament, Team


def compute_team_stats(team_id: str, tournaments: list[Tournament]) -> dict:
    stats = {
        "tournaments_played": 0,
        "tournaments_won": 0,
        "podiums": 0,        # top 3
        "total_points": 0.0,
        "matches_played": 0,
        "matches_won": 0,
        "matches_lost": 0,
        "trophies": [],      # [{tournament_name, date, image_filename, importance_label}]
        "history": [],       # [{tournament_name, date, position_label, points}]
    }

    for t in tournaments:
        participates = any(tm.id == team_id for tm in t.teams)
        if not participates:
            continue

        for stage in t.stages:
            for m in stage.matches:
                if not m.played or m.bye:
                    continue
                if m.team1_id == team_id:
                    stats["matches_played"] += 1
                    if m.winner_id == team_id:
                        stats["matches_won"] += 1
                    elif m.winner_id:
                        stats["matches_lost"] += 1
                elif m.team2_id == team_id:
                    stats["matches_played"] += 1
                    if m.winner_id == team_id:
                        stats["matches_won"] += 1
                    elif m.winner_id:
                        stats["matches_lost"] += 1

        if t.status != "finished":
            continue

        entry = next((r for r in t.final_standings if r["team_id"] == team_id), None)
        if not entry:
            continue

        stats["tournaments_played"] += 1
        stats["total_points"] += entry["points"]
        pos_label = str(entry["position_from"]) if entry["position_from"] == entry["position_to"] \
            else f"{entry['position_from']}-{entry['position_to']}"
        stats["history"].append({
            "tournament_name": t.name, "date": t.date,
            "position_label": pos_label, "points": entry["points"],
        })

        if entry["position_from"] <= 3:
            stats["podiums"] += 1
        if entry["position_from"] == 1 and entry["position_to"] == 1:
            stats["tournaments_won"] += 1
            stats["trophies"].append({
                "tournament_name": t.name, "date": t.date,
                "image_filename": t.trophy_image, "importance_label": t.importance_label,
            })

    stats["total_points"] = round(stats["total_points"], 1)
    stats["win_rate"] = round(100 * stats["matches_won"] / stats["matches_played"], 1) \
        if stats["matches_played"] else 0.0
    stats["history"].sort(key=lambda h: h["date"], reverse=True)
    return stats
