"""Reparto de puntos segun la posicion final y la importancia del torneo."""
from __future__ import annotations
from .models import PointsRange


def default_points_table(num_teams: int) -> list[PointsRange]:
    """Genera una plantilla razonable de puntos segun el numero de equipos."""
    if num_teams <= 4:
        template = [(1, 1, 100), (2, 2, 60), (3, 4, 30)]
    elif num_teams <= 8:
        template = [(1, 1, 100), (2, 2, 70), (3, 4, 45), (5, 8, 20)]
    else:
        template = [(1, 1, 100), (2, 2, 70), (3, 4, 45), (5, 8, 25), (9, 16, 10)]
    return [PointsRange(f, t, p) for (f, t, p) in template]


def points_for_position(points_table: list[PointsRange], position: int) -> int:
    for pr in points_table:
        if pr.pos_from <= position <= pr.pos_to:
            return pr.points
    return 0


def points_for_range(points_table: list[PointsRange], pos_from: int, pos_to: int) -> float:
    """Si una posicion final es un empate (rango), se promedian los puntos de cada posicion del rango."""
    vals = [points_for_position(points_table, p) for p in range(pos_from, pos_to + 1)]
    return sum(vals) / len(vals) if vals else 0
