"""Prüfer für Tischpläne: Begegnungszähler, Wiederholungen, Abdeckung, Einzelpersonen. Reine Standardbibliothek."""

from dataclasses import dataclass
from itertools import combinations


def pair_counts(plan, n: int) -> list:
    """n×n-Zähler: wie oft saßen a und b zusammen an einem Tisch."""
    cnt = [[0] * n for _ in range(n)]
    for rnd in plan:
        for table in rnd:
            for a, b in combinations(table, 2):
                cnt[a][b] += 1
                cnt[b][a] += 1
    return cnt


@dataclass(frozen=True)
class PlanMetrics:
    rounds: int
    repeats: int            # überzählige Begegnungen: Summe über Paare von max(Begegnungen − 1, 0)
    same_dept: int          # Begegnungen von Paaren derselben Abteilung
    cross_pairs: int        # Zahl der Paare aus verschiedenen Abteilungen
    covered: int            # davon mindestens einmal begegnet
    singles: int            # Tische mit nur einer Person (über alle Runden)
    size_min: int
    size_max: int
    tables_min: int         # Tische je Runde
    tables_max: int
    partition_ok: bool      # jede Runde setzt jede Person genau einmal

    @property
    def coverage(self) -> float:
        return 0.0 if self.cross_pairs == 0 else self.covered / self.cross_pairs


def analyse_plan(plan, s: int, m: int) -> PlanMetrics:
    n = s * m
    cnt = pair_counts(plan, n)
    repeats = same = covered = 0
    for a in range(n):
        for b in range(a + 1, n):
            c = cnt[a][b]
            if c > 1:
                repeats += c - 1
            if a // m == b // m:
                same += c
            elif c > 0:
                covered += 1
    cross_pairs = n * (n - 1) // 2 - s * (m * (m - 1) // 2)
    sizes = [len(t) for rnd in plan for t in rnd] or [0]
    per_round = [len(rnd) for rnd in plan] or [0]
    ok = all(sorted(p for t in rnd for p in t) == list(range(n)) for rnd in plan)
    return PlanMetrics(len(plan), repeats, same, cross_pairs, covered, sum(1 for z in sizes if z == 1),
                       min(sizes), max(sizes), min(per_round), max(per_round), ok)


def repeat_free_prefix(plan, n: int) -> int:
    """Wie viele Runden vom Anfang an enthalten keine Wiederholung (Plan wird Runde für Runde aufgebaut)."""
    met = [[False] * n for _ in range(n)]
    for r, rnd in enumerate(plan):
        pairs = [pr for table in rnd for pr in combinations(table, 2)]
        if any(met[a][b] for a, b in pairs):
            return r
        for a, b in pairs:
            met[a][b] = met[b][a] = True
    return len(plan)
