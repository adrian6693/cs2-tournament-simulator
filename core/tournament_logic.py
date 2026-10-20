"""Logica de negocio: crear etapas, registrar resultados, avanzar rondas/etapas y cerrar el torneo."""
from __future__ import annotations
import random
from . import seeding, standings, points as points_mod
from .models import Tournament, Stage, Match, new_id

STAGE_TYPES = {
    "round_robin": "Round Robin (liga)",
    "single_elim": "Eliminacion directa",
    "swiss": "Suizo",
}


def start_stage(tournament: Tournament, stage: Stage):
    """Genera los primeros enfrentamientos de una etapa a partir de stage.participants (orden = seed)."""
    bo = stage.config.get("bo", 1)
    if stage.type == "single_elim":
        stage.matches = seeding.single_elim_first_round(stage.participants, bo=bo)
    elif stage.type == "round_robin":
        double = stage.config.get("double_round", False)
        num_groups = stage.config.get("num_groups", 1)
        if num_groups and num_groups > 1:
            groups = seeding.assign_groups(stage.participants, num_groups)
            stage.config["groups"] = groups
            all_matches = []
            for label, team_ids in groups.items():
                group_matches = seeding.round_robin_schedule(team_ids, bo=bo, double_round=double)
                for m in group_matches:
                    m.group = label
                all_matches.extend(group_matches)
            stage.matches = all_matches
        else:
            stage.config.pop("groups", None)
            stage.matches = seeding.round_robin_schedule(stage.participants, bo=bo, double_round=double)
    elif stage.type == "swiss":
        stage.matches = seeding.swiss_round1(stage.participants, bo=bo)
    stage.finished = False


def record_result(stage: Stage, match_id: str, score1: int, score2: int):
    m = next(mt for mt in stage.matches if mt.id == match_id)
    m.score1, m.score2 = score1, score2
    m.played = True
    if score1 > score2:
        m.winner_id = m.team1_id
    elif score2 > score1:
        m.winner_id = m.team2_id
    else:
        m.winner_id = None  # empate no permitido normalmente, pero no forzamos


def current_round(stage: Stage) -> int:
    return max((m.round for m in stage.matches), default=0)


def round_is_complete(stage: Stage, round_num: int) -> bool:
    round_matches = [m for m in stage.matches if m.round == round_num]
    return len(round_matches) > 0 and all(m.played for m in round_matches)


def bracket_is_complete(stage: Stage) -> bool:
    rnd = current_round(stage)
    round_matches = [m for m in stage.matches if m.round == rnd]
    return len(round_matches) == 1 and round_matches[0].played


def swiss_rounds_target(num_participants: int) -> int:
    import math
    return max(3, math.ceil(math.log2(max(num_participants, 2))))


def advance_round_if_ready(stage: Stage):
    """Para single_elim y swiss: si la ronda actual esta completa y la etapa no ha terminado, crea la siguiente."""
    rnd = current_round(stage)
    if not round_is_complete(stage, rnd):
        return
    bo = stage.config.get("bo", 1)
    if stage.type == "single_elim":
        if bracket_is_complete(stage):
            stage.finished = True
            return
        round_matches = [m for m in stage.matches if m.round == rnd]
        new_matches = seeding.single_elim_next_round(round_matches, rnd + 1, bo=bo)
        stage.matches.extend(new_matches)
    elif stage.type == "swiss":
        target_rounds = stage.config.get("rounds") or swiss_rounds_target(len(stage.participants))
        if rnd >= target_rounds:
            stage.finished = True
            return
        current_standings = standings.swiss_standings(stage)
        played_pairs = set()
        for m in stage.matches:
            if m.team1_id and m.team2_id:
                played_pairs.add(frozenset((m.team1_id, m.team2_id)))
        new_matches = seeding.swiss_next_round(current_standings, played_pairs, rnd + 1, bo=bo)
        stage.matches.extend(new_matches)
    elif stage.type == "round_robin":
        stage.finished = standings.stage_is_finished(stage)


def finalize_stage_standings(stage: Stage):
    stage.standings = standings.compute_stage_standings(stage)


def randomize_pending_matches(stage: Stage) -> int:
    """Asigna un resultado aleatorio a todos los partidos de la etapa que aun no tengan resultado
    (sin tocar los que ya estan jugados), avanzando de ronda automaticamente si hace falta.
    Devuelve el numero de partidos que se han rellenado."""
    filled = 0
    while True:
        pending = [m for m in stage.matches
                   if not m.played and not m.bye and m.team1_id and m.team2_id]
        if not pending:
            break
        for m in pending:
            bo = max(m.bo, 1)
            win_score = bo // 2 + 1
            lose_score = random.randint(0, win_score - 1)
            if random.random() < 0.5:
                record_result(stage, m.id, win_score, lose_score)
            else:
                record_result(stage, m.id, lose_score, win_score)
            filled += 1
        advance_round_if_ready(stage)
        if stage.finished:
            break
    return filled


def build_next_stage_participants(prev_stage: Stage, advance_count: int) -> list[str]:
    """Ordena los equipos que avanzan a la siguiente etapa segun su posicion en la etapa anterior."""
    ordered = sorted(prev_stage.standings, key=lambda r: r["position"])
    return [r["team_id"] for r in ordered[:advance_count]]


def compute_final_standings(tournament: Tournament):
    """Combina las etapas para obtener la clasificacion final y reparte puntos."""
    stages = tournament.stages
    last_stage = stages[-1]
    finalize_stage_standings(last_stage)

    position_map = {}  # team_id -> (pos_from, pos_to)
    for r in last_stage.standings:
        position_map[r["team_id"]] = (r["position_from"], r["position_to"])

    if len(stages) > 1:
        # los equipos eliminados en la etapa 1 (no avanzaron) van despues de todos los de la etapa 2
        first_stage = stages[0]
        advanced = set(last_stage.participants)
        finalize_stage_standings(first_stage)
        offset = len(last_stage.participants)
        eliminated = [r for r in first_stage.standings if r["team_id"] not in advanced]
        # se reordenan por su posicion original en la fase 1 y se les añade el offset de la fase 2
        eliminated_sorted = sorted(eliminated, key=lambda r: r["position_from"])
        cursor = offset + 1
        i = 0
        while i < len(eliminated_sorted):
            j = i
            while j + 1 < len(eliminated_sorted) and eliminated_sorted[j + 1]["position_from"] == eliminated_sorted[i]["position_from"]:
                j += 1
            span = cursor + (j - i)
            for k in range(i, j + 1):
                position_map[eliminated_sorted[k]["team_id"]] = (cursor, span)
            cursor = span + 1
            i = j + 1

    final_list = []
    for tid, (pf, pt) in position_map.items():
        pts = points_mod.points_for_range(tournament.points_table, pf, pt) * tournament.importance
        final_list.append({"team_id": tid, "position_from": pf, "position_to": pt, "points": round(pts, 1)})
    final_list.sort(key=lambda r: r["position_from"])
    tournament.final_standings = final_list
    tournament.status = "finished"
