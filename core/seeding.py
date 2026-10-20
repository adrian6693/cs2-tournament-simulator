"""Generacion de enfrentamientos: eliminacion directa, round robin y suizo."""
from __future__ import annotations
from .models import Match, new_id


def _next_power_of_two(n: int) -> int:
    p = 1
    while p < n:
        p *= 2
    return p


def _standard_bracket_order(size: int) -> list[int]:
    """Devuelve el orden de seeds (1..size) para un cuadro de 'size' plazas,
    de forma que los mejores seeds queden lo mas separados posible (seeding proporcional)."""
    order = [1]
    while len(order) < size:
        new_order = []
        n = len(order) * 2
        for s in order:
            new_order.append(s)
            new_order.append(n + 1 - s)
        order = new_order
    return order


def single_elim_first_round(participants: list[str], bo: int = 1) -> list[Match]:
    """participants: lista de team_id ordenada por seed (1er elemento = seed 1).
    Devuelve los partidos de la primera ronda, metiendo BYE a los mejores seeds si
    el numero de equipos no es potencia de 2."""
    n = len(participants)
    size = _next_power_of_two(n)
    order = _standard_bracket_order(size)  # posiciones ocupadas por seed 1..size

    def team_for_seed(seed):
        idx = seed - 1
        return participants[idx] if idx < n else None  # None = BYE

    slots = [team_for_seed(s) for s in order]

    matches = []
    slot_num = 0
    for i in range(0, size, 2):
        t1, t2 = slots[i], slots[i + 1]
        is_bye = (t1 is None) or (t2 is None)
        m = Match(id=new_id(), round=1, slot=slot_num, team1_id=t1, team2_id=t2, bo=bo, bye=is_bye)
        if is_bye:
            m.winner_id = t1 if t1 is not None else t2
            m.played = True
        matches.append(m)
        slot_num += 1
    return matches


def single_elim_next_round(prev_round_matches: list[Match], round_num: int, bo: int = 1) -> list[Match]:
    """A partir de los ganadores de la ronda anterior (ordenados por slot), genera la siguiente ronda."""
    winners = [m.winner_id for m in sorted(prev_round_matches, key=lambda m: m.slot)]
    matches = []
    slot_num = 0
    for i in range(0, len(winners), 2):
        t1, t2 = winners[i], winners[i + 1]
        m = Match(id=new_id(), round=round_num, slot=slot_num, team1_id=t1, team2_id=t2, bo=bo)
        prev1 = sorted(prev_round_matches, key=lambda m: m.slot)[i]
        prev2 = sorted(prev_round_matches, key=lambda m: m.slot)[i + 1]
        m.from_match1, m.from_match2 = prev1.id, prev2.id
        matches.append(m)
        slot_num += 1
    return matches


def assign_groups(participants: list[str], num_groups: int) -> dict:
    """Reparte a los equipos en N grupos usando distribucion en serpentina
    (seed 1 al grupo A, seed 2 al B... y al llegar al final se invierte),
    para que cada grupo quede lo mas equilibrado posible segun el seeding."""
    labels = [chr(ord('A') + i) for i in range(num_groups)]
    groups = {label: [] for label in labels}
    g = 0
    direction = 1
    for team_id in participants:
        groups[labels[g]].append(team_id)
        g += direction
        if g == num_groups:
            g = num_groups - 1
            direction = -1
        elif g < 0:
            g = 0
            direction = 1
    return groups


def round_robin_schedule(participants: list[str], bo: int = 1, double_round: bool = False) -> list[Match]:
    """Metodo del circulo. Si el numero de equipos es impar se añade un 'fantasma' (descansa cada ronda)."""
    teams = list(participants)
    bye_team = None
    if len(teams) % 2 == 1:
        bye_team = "__BYE__"
        teams.append(bye_team)

    n = len(teams)
    rounds = n - 1
    fixed = teams[0]
    rotating = teams[1:]

    all_matches = []
    slot_counter = 0
    schedule_sets = []
    for r in range(rounds):
        round_teams = [fixed] + rotating
        pairs = []
        for i in range(n // 2):
            a, b = round_teams[i], round_teams[n - 1 - i]
            pairs.append((a, b))
        schedule_sets.append(pairs)
        rotating = [rotating[-1]] + rotating[:-1]

    passes = [schedule_sets]
    if double_round:
        # segunda vuelta con los locales/visitantes invertidos
        reversed_sets = [[(b, a) for (a, b) in rnd] for rnd in schedule_sets]
        passes.append(reversed_sets)

    round_num = 1
    for pass_sets in passes:
        for pairs in pass_sets:
            for (a, b) in pairs:
                if a == bye_team or b == bye_team:
                    continue
                m = Match(id=new_id(), round=round_num, slot=slot_counter, team1_id=a, team2_id=b, bo=bo)
                all_matches.append(m)
                slot_counter += 1
            round_num += 1
    return all_matches


def swiss_round1(participants: list[str], bo: int = 1) -> list[Match]:
    """Primera ronda suiza: mitad superior del seeding contra mitad inferior (1 vs n/2+1, etc.)."""
    n = len(participants)
    half = (n + 1) // 2
    top = participants[:half]
    bottom = participants[half:]
    matches = []
    slot = 0
    for i, t1 in enumerate(top):
        t2 = bottom[i] if i < len(bottom) else None
        m = Match(id=new_id(), round=1, slot=slot, team1_id=t1, team2_id=t2, bo=bo, bye=(t2 is None))
        if t2 is None:
            m.winner_id = t1
            m.played = True
        matches.append(m)
        slot += 1
    return matches


def swiss_next_round(standings: list[dict], played_pairs: set, round_num: int, bo: int = 1) -> list[Match]:
    """standings: lista de dicts {team_id, wins, losses} ordenada de mejor a peor.
    Empareja dentro del mismo grupo de record evitando repetir rivales (algoritmo goloso)."""
    # agrupar por record (wins, losses)
    groups = {}
    for s in standings:
        key = (s["wins"], s["losses"])
        groups.setdefault(key, []).append(s["team_id"])

    pending = []
    leftover = None
    for key in sorted(groups.keys(), key=lambda k: (-k[0], k[1])):
        group = groups[key]
        if leftover is not None:
            group = [leftover] + group
            leftover = None
        pending.extend(_pair_group_avoiding_repeats(group, played_pairs))
        # si el grupo tenia numero impar, el ultimo sin emparejar baja al siguiente grupo
        used = set()
        for a, b in pending:
            used.add(a); used.add(b)
        unpaired = [t for t in group if t not in used]
        if unpaired:
            leftover = unpaired[0]

    matches = []
    slot = 0
    for (t1, t2) in pending:
        m = Match(id=new_id(), round=round_num, slot=slot, team1_id=t1, team2_id=t2, bo=bo)
        matches.append(m)
        slot += 1
    if leftover is not None:
        m = Match(id=new_id(), round=round_num, slot=slot, team1_id=leftover, team2_id=None, bo=bo,
                   bye=True, winner_id=leftover, played=True)
        matches.append(m)
    return matches


def _pair_group_avoiding_repeats(group: list[str], played_pairs: set) -> list[tuple]:
    group = list(group)
    pairs = []
    while len(group) >= 2:
        a = group.pop(0)
        chosen = None
        for b in group:
            if frozenset((a, b)) not in played_pairs:
                chosen = b
                break
        if chosen is None:
            chosen = group[0]
        group.remove(chosen)
        pairs.append((a, chosen))
    return pairs
