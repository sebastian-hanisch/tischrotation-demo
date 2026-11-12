"""Koordinator der Verfahren: führt Konstruktion, Auffüllen, Suche, Greedy und Zufall für eine Feier aus und prüft jedes Ergebnis.

Jedes Verfahren ist eine eigene Funktion in `trt_designs.py` bzw. `trt_search.py`; hier steht nur das Zusammenspiel und der Vergleich in derselben Zähleinheit:
**Runden ohne Wiederholung** (Zufall: Mittel über Zufallsfolgen, Greedy: Median über Zufalls-Seeds, die übrigen: das Ergebnis des Laufs)."""

from dataclasses import dataclass
from statistics import mean, median

import trt_constants as C
import trt_designs as D
import trt_search as S
from trt_check import PlanMetrics, analyse_plan, repeat_free_prefix
from trt_field import is_prime_power

KEYS = ("konstruktion", "auffuellen", "suche", "greedy", "zufall")
LABELS = {
    "konstruktion": "Körper-Konstruktion",
    "auffuellen": "Auffüllen und Streichen",
    "suche": "Suche (Annealing)",
    "greedy": "Greedy (Runde für Runde)",
    "zufall": "Zufall",
}


@dataclass(frozen=True)
class MethodResult:
    key: str
    available: bool
    value: float          # Runden ohne Wiederholung (Statistik laut `stat`)
    stat: str             # „Lauf“, „Mittel über 200 Zufallsfolgen“, „Median über 5 Zufalls-Seeds“
    plan: tuple           # ein gezeigter Plan (Zufall und Greedy: der des ersten Zufalls-Seeds)
    metrics: PlanMetrics | None
    note: str

    @property
    def label(self) -> str:
        return LABELS[self.key]


def _result(key, plan, value, stat, s, m, note="") -> MethodResult:
    metrics = analyse_plan(plan, s, m)
    return MethodResult(key, True, float(value), stat, tuple(tuple(tuple(t) for t in rnd) for rnd in plan), metrics, note)


def _missing(key, note) -> MethodResult:
    return MethodResult(key, False, 0.0, "", (), None, note)


def construction_result(s: int, m: int) -> MethodResult:
    if D.construction_available(s, m):
        plan = D.construction_plan(s, m)
        return _result("konstruktion", plan, len(plan), "Konstruktion", s, m)
    if not is_prime_power(m):
        return _missing("konstruktion", f"m = {m} ist keine Primzahlpotenz: die Körper-Konstruktion braucht einen Körper mit m Elementen.")
    return _missing("konstruktion", f"s = {s} Abteilungen sind mehr als m = {m} Personen je Abteilung: bei {m} Tischen zu {s} gibt es nur eine Runde ohne Wiederholung (die {s} Personen eines Tisches müssten sich auf {m} < {s} Tische verteilen), die Konstruktion braucht s ≤ m.")


def fill_result(s: int, m: int) -> MethodResult:
    q, plan = D.fill_plan(s, m)
    note = f"Körper mit q = {q} Elementen, {q - m} Person(en) je Abteilung gestrichen."
    return _result("auffuellen", plan, len(plan), "Konstruktion", s, m, note)


def search_result(s: int, m: int, seed: int, iters: int) -> MethodResult:
    plan, log = S.anneal_rounds(s, m, seed, iters)
    if len(plan) >= m:
        note = f"Die Schranke von {m} Runden ist erreicht."
    else:
        note = f"Bei {len(plan) + 1} Runden blieben {log[-1][1]} Wiederholungen nach {log[-1][2]:,} Zugvorschlägen.".replace(",", ".")
    return _result("suche", plan, len(plan), "ein Lauf", s, m, note)


def greedy_result(s: int, m: int, seed: int) -> MethodResult:
    plans = [S.greedy_rounds(s, m, seed * C.SUBSEED_STRIDE + k, C.NODE_LIMIT) for k in range(C.GREEDY_SEEDS)]
    value = median(len(p) for p, _ in plans)
    reasons = {why for _, why in plans}
    note = "Abbruch: " + ", ".join(sorted(reasons)) + "."
    return _result("greedy", plans[0][0], value, f"Median über {C.GREEDY_SEEDS} Zufalls-Seeds", s, m, note)


def random_result(s: int, m: int, seed: int) -> MethodResult:
    plans = [S.random_rounds(s, m, seed * C.SUBSEED_STRIDE + k) for k in range(C.RANDOM_TRIALS)]
    value = mean(len(p) for p in plans)
    return _result("zufall", plans[0], value, f"Mittel über {C.RANDOM_TRIALS} Zufallsfolgen", s, m)


def run_all(s: int, m: int, seed: int, fill: bool, iters: int) -> dict:
    """Alle Verfahren für (s, m); Suche, Greedy und Zufall nur bis N_LIVE_MAX Personen (darüber stehen sie in den vorgerechneten Experimenten)."""
    out = {"konstruktion": construction_result(s, m)}
    out["auffuellen"] = fill_result(s, m) if fill else _missing("auffuellen", "Ausgeschaltet: Schalter „Zusätzliche Tische erlauben“ in der Seitenleiste.")
    if s * m <= C.N_LIVE_MAX:
        out["suche"] = search_result(s, m, seed, iters)
        out["greedy"] = greedy_result(s, m, seed)
        out["zufall"] = random_result(s, m, seed)
    else:
        note = f"Mehr als {C.N_LIVE_MAX} Personen: nur in den vorgerechneten Experimenten."
        for key in ("suche", "greedy", "zufall"):
            out[key] = _missing(key, note)
    return out


def verify_prefix(plan, s: int, m: int) -> int:
    """Unabhängiger Zähler der wiederholungsfreien Runden eines Plans (für Tests)."""
    return repeat_free_prefix([list(map(list, rnd)) for rnd in plan], s * m)
