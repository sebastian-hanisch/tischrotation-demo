"""Suchverfahren für die Abteilungsmischung: Zufall, Greedy (exakte Runde für Runde) und Simulated Annealing mit wachsender Rundenzahl.

Person p = d·m + i; ein Tisch ist eine Liste mit einer Person je Abteilung, an Stelle d steht die Person der Abteilung d. Alle Verfahren sind mit festem Zufalls-Seed
reproduzierbar (SplitMix64) und laufen ohne Zeitlimit: das Budget ist eine Zahl von Zugvorschlägen bzw. Knoten, nicht von Sekunden."""

import math
from itertools import combinations

from trt_check import pair_counts, repeat_free_prefix
from trt_rng import SplitMix64


def random_round(s: int, m: int, rng: SplitMix64) -> list:
    """Zufällige Runde: in jeder Abteilung eine zufällige Zuordnung der Personen zu den m Tischen."""
    tables = [[0] * s for _ in range(m)]
    for d in range(s):
        order = list(range(m))
        rng.shuffle(order)
        for t in range(m):
            tables[t][d] = d * m + order[t]
    return tables


def random_rounds(s: int, m: int, seed: int) -> list:
    """Zufällige Runden, solange keine Wiederholung entsteht: die Runden vor der ersten Wiederholung (mindestens eine)."""
    rng = SplitMix64(seed)
    n = s * m
    plan = []
    while len(plan) <= m:
        candidate = random_round(s, m, rng)
        if repeat_free_prefix(plan + [candidate], n) < len(plan) + 1:
            break
        plan.append(candidate)
    return plan


def _find_round(s: int, m: int, met: list, rng: SplitMix64, node_limit: int):
    """Eine zulässige Runde (kein Paar, das sich schon begegnet ist) per Tiefensuche mit Zurücksetzen. Ergebnis: (Runde oder None, Knotenlimit erreicht)."""
    tables = [[-1] * s for _ in range(m)]
    for i in range(m):
        tables[i][0] = i  # Abteilung 0: Person i an Tisch i (Tische sind nicht unterscheidbar)
    order = []
    for d in range(1, s):
        persons = list(range(d * m, (d + 1) * m))
        rng.shuffle(persons)
        order += [(d, p) for p in persons]
    state = {"nodes": 0, "limit": False}

    def place(k):
        if k == len(order):
            return True
        state["nodes"] += 1
        if state["nodes"] > node_limit:
            state["limit"] = True
            return False
        d, p = order[k]
        free = [t for t in range(m) if tables[t][d] < 0 and all(not (met[p] >> x) & 1 for x in tables[t][:d])]
        rng.shuffle(free)
        for t in free:
            tables[t][d] = p
            if place(k + 1):
                return True
            tables[t][d] = -1
            if state["limit"]:
                return False
        return False

    if place(0):
        return tables, False
    return None, state["limit"]


def greedy_rounds(s: int, m: int, seed: int, node_limit: int = 30000):
    """Greedy: jede Runde ist eine (zufällige) zulässige Runde bezüglich aller früheren; bricht ab, wenn keine mehr gefunden wird.

    Ergebnis (Plan, Grund): Grund "vollständig" (die Suche in dieser Runde war erschöpfend, es gibt keine zulässige Runde mehr),
    "Knotenlimit" (nicht entschieden) oder "alle" (m Runden: mehr gibt es nicht)."""
    rng = SplitMix64(seed)
    n = s * m
    met = [0] * n
    plan = []
    while len(plan) < m:
        rnd, limit = _find_round(s, m, met, rng, node_limit)
        if rnd is None:
            return plan, ("Knotenlimit" if limit else "vollständig")
        for table in rnd:
            for a, b in combinations(table, 2):
                met[a] |= 1 << b
                met[b] |= 1 << a
        plan.append(rnd)
    return plan, "alle"


def anneal(base: list, w: int, s: int, m: int, rng: SplitMix64, iters: int, temperature: float = 0.25):
    """Simulated Annealing mit w Runden: Zug = zwei Personen derselben Abteilung in verschiedenen Tischen derselben Runde tauschen.

    Kosten = überzählige Begegnungen (Summe über Paare von max(Begegnungen − 1, 0)). Startplan `base` (höchstens w Runden), fehlende Runden zufällig.
    Ergebnis (Plan, Kosten, Züge)."""
    n = s * m
    tabs = [[list(t) for t in rnd] for rnd in base]
    while len(tabs) < w:
        tabs.append(random_round(s, m, rng))
    grp = [[0] * n for _ in range(w)]
    for r in range(w):
        for t, table in enumerate(tabs[r]):
            for p in table:
                grp[r][p] = t
    cnt = pair_counts(tabs, n)
    cost = sum(max(cnt[a][b] - 1, 0) for a in range(n) for b in range(a + 1, n))
    best_cost = cost
    best = [[list(t) for t in rnd] for rnd in tabs]
    if cost == 0:
        return best, 0, 0
    expneg = {d: math.exp(-d / temperature) for d in range(1, 12)}
    moves = 0
    for moves in range(1, iters + 1):
        r = rng.below(w)
        a = rng.below(n)
        ga = grp[r][a]
        ca = cnt[a]
        ta = tabs[r][ga]
        # Fokus: fast nur Personen mit einer Wiederholung bewegen
        if not any(ca[c] >= 2 for c in ta if c != a) and rng.random() < 0.95:
            continue
        gb = rng.below(m - 1)
        if gb >= ga:
            gb += 1
        d = a // m
        tb = tabs[r][gb]
        b = tb[d]
        cb = cnt[b]
        delta = 0
        for c in ta:
            if c != a:
                if ca[c] >= 2:
                    delta -= 1
                if cb[c] >= 1:
                    delta += 1
        for c in tb:
            if c != b:
                if cb[c] >= 2:
                    delta -= 1
                if ca[c] >= 1:
                    delta += 1
        if delta <= 0 or rng.random() < expneg.get(delta, 0.0):
            for c in ta:
                if c != a:
                    ca[c] -= 1
                    cnt[c][a] -= 1
                    cb[c] += 1
                    cnt[c][b] += 1
            for c in tb:
                if c != b:
                    cb[c] -= 1
                    cnt[c][b] -= 1
                    ca[c] += 1
                    cnt[c][a] += 1
            ta[d] = b
            tb[d] = a
            grp[r][a] = gb
            grp[r][b] = ga
            cost += delta
            if cost < best_cost:
                best_cost = cost
                best = [[list(t) for t in rnd] for rnd in tabs]
                if cost == 0:
                    break
    return best, best_cost, moves


def anneal_rounds(s: int, m: int, seed: int, iters_per_round: int = 1_000_000):
    """Rundenzahl schrittweise erhöhen: die Lösung für w − 1 Runden plus eine Zufallsrunde wird per Annealing repariert; Abbruch beim ersten w ohne Lösung.

    Ergebnis (Plan mit lauter wiederholungsfreien Runden, Protokoll [(w, Restkosten, Züge)])."""
    rng = SplitMix64(seed)
    plan = []
    log = []
    w = 1
    while w <= m:
        best, cost, moves = anneal(plan, w, s, m, rng, iters_per_round)
        log.append((w, cost, moves))
        if cost > 0:
            break
        plan = best
        w += 1
    return plan, log
