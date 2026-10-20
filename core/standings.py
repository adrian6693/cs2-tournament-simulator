"""Calculo de standings (clasificacion) dentro de una etapa."""
from __future__ import annotations
from .models import Stage


def _compute_records(team_ids: list, matches: list) -> list[dict]:
    records = {tid: {"team_id": tid, "wins": 0, "losses": 0, "score_diff": 0} for tid in team_ids}
    for m in matches:
        if not m.played or m.team1_id is None or m.team2_id is None:
            continue
        if m.team1_id not in records or m.team2_id not in records:
            continue
        r1, r2 = records[m.team1_id], records[m.team2_id]
        r1["score_diff"] += (m.score1 - m.score2)
        r2["score_diff"] += (m.score2 - m.score1)
        if m.winner_id == m.team1_id:
            r1["wins"] += 1; r2["losses"] += 1
        elif m.winner_id == m.team2_id:
            r2["wins"] += 1; r1["losses"] += 1
    return list(records.values())


def round_robin_standings(stage: Stage) -> list[dict]:
    groups_cfg = stage.config.get("groups")

    if not groups_cfg:
        records = _compute_records(stage.participants, stage.matches)
        ordered = sorted(records, key=lambda r: (-r["wins"], -r["score_diff"]))
        return _assign_tied_positions(ordered, key=lambda r: (r["wins"], r["score_diff"]))

    # con grupos: se calcula la clasificacion dentro de cada grupo y luego se combinan
    # (los 1os de cada grupo empatan por la posicion 1, los 2os por la siguiente, etc.)
    local_results = []
    for label, team_ids in groups_cfg.items():
        group_matches = [m for m in stage.matches if m.group == label]
        records = _compute_records(team_ids, group_matches)
        ordered = sorted(records, key=lambda r: (-r["wins"], -r["score_diff"]))
        tagged = _assign_tied_positions(ordered, key=lambda r: (r["wins"], r["score_diff"]))
        for r in tagged:
            r["group"] = label
        local_results.extend(tagged)

    local_results.sort(key=lambda r: (r["position"], -r["wins"], -r["score_diff"]))
    return _assign_tied_positions(local_results, key=lambda r: (r["position"], r["wins"], r["score_diff"]))


def group_standings_live(stage: Stage) -> dict:
    """Clasificacion actual (parcial, sin esperar a que termine la etapa) de cada grupo,
    para mostrarla en la interfaz mientras se juega."""
    groups_cfg = stage.config.get("groups") or {}
    result = {}
    for label, team_ids in groups_cfg.items():
        group_matches = [m for m in stage.matches if m.group == label]
        records = _compute_records(team_ids, group_matches)
        records.sort(key=lambda r: (-r["wins"], -r["score_diff"]))
        result[label] = records
    return result


def swiss_standings(stage: Stage) -> list[dict]:
    # Es el mismo calculo que round robin (wins/losses), simplemente sobre las rondas suizas jugadas.
    return round_robin_standings(stage)


def single_elim_standings(stage: Stage) -> list[dict]:
    """Calcula posiciones finales de un cuadro de eliminacion directa.
    1: campeon, 2: subcampeon, 3-4: semifinalistas perdedores, 5-8: cuartos, etc."""
    matches_by_round = {}
    for m in stage.matches:
        matches_by_round.setdefault(m.round, []).append(m)
    if not matches_by_round:
        return []
    max_round = max(matches_by_round.keys())
    final_matches = matches_by_round[max_round]
    final = final_matches[0]
    positions = []
    if final.played and final.winner_id:
        champion = final.winner_id
        runner_up = final.team1_id if final.winner_id == final.team2_id else final.team2_id
        positions.append({"team_id": champion, "position": 1})
        if runner_up:
            positions.append({"team_id": runner_up, "position": 2})

    # perdedores de cada ronda anterior, agrupados: ronda N-1 -> posicion 3-4, ronda N-2 -> 5-8, etc.
    already = {p["team_id"] for p in positions}
    pos_cursor = 3
    for rnd in range(max_round - 1, 0, -1):
        losers = []
        for m in matches_by_round.get(rnd, []):
            if m.bye:
                continue
            if m.played and m.winner_id:
                loser = m.team1_id if m.winner_id == m.team2_id else m.team2_id
                if loser and loser not in already:
                    losers.append(loser)
        if losers:
            span = pos_cursor + len(losers) - 1
            for tid in losers:
                positions.append({"team_id": tid, "position_from": pos_cursor, "position_to": span,
                                   "position": pos_cursor})
                already.add(tid)
        pos_cursor += max(len(matches_by_round.get(rnd, [])), 1)
    return positions


def _assign_tied_positions(ordered: list[dict], key) -> list[dict]:
    result = []
    i = 0
    pos = 1
    while i < len(ordered):
        j = i
        while j + 1 < len(ordered) and key(ordered[j + 1]) == key(ordered[i]):
            j += 1
        span_from, span_to = pos, pos + (j - i)
        for k in range(i, j + 1):
            item = dict(ordered[k])
            item["position_from"] = span_from
            item["position_to"] = span_to
            item["position"] = span_from
            result.append(item)
        pos = span_to + 1
        i = j + 1
    return result


def compute_stage_standings(stage: Stage) -> list[dict]:
    if stage.type == "round_robin":
        return round_robin_standings(stage)
    if stage.type == "swiss":
        return swiss_standings(stage)
    if stage.type == "single_elim":
        res = single_elim_standings(stage)
        for r in res:
            r.setdefault("position_from", r["position"])
            r.setdefault("position_to", r["position"])
        return res
    return []


def stage_is_finished(stage: Stage) -> bool:
    if not stage.matches:
        return False
    return all(m.played for m in stage.matches)
