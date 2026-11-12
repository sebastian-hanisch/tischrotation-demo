"""Kennzahlen, Verdikte (reine Funktionen) und Zugriff auf die vorgerechneten Experimente."""

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import trt_algorithm as A
import trt_constants as C

RESULTS_PATH = Path(__file__).resolve().parent / "data" / "trt_results.json"


@dataclass(frozen=True)
class Settings:
    s: int = C.DEFAULT_S
    m: int = C.DEFAULT_M
    seed: int = C.DEFAULT_SEED
    fill: bool = False
    budget: int = C.DEFAULT_BUDGET


@dataclass(frozen=True)
class Analysis:
    settings: Settings
    results: dict  # Schlüssel aus trt_algorithm.KEYS

    @property
    def bound(self) -> int:
        """Schranke für m Tische zu s Personen: nach m Runden kennt jede Person alle Fremden, die (m + 1)-te Runde enthält eine Wiederholung;
        bei s > m gibt es sogar nur eine Runde (die s Personen eines Tisches müssten sich in der nächsten Runde auf m < s Tische verteilen, also sitzen zwei wieder zusammen)."""
        return self.settings.m if self.settings.s <= self.settings.m else 1

    def best_key(self):
        """Das Verfahren mit den meisten wiederholungsfreien Runden unter den deterministischen Plänen (Konstruktion, Auffüllen, Suche); bei Gleichstand die frühere."""
        keys = [k for k in ("konstruktion", "auffuellen", "suche") if self.results[k].available]
        if not keys:
            return None
        return max(keys, key=lambda k: (self.results[k].value, -keys.index(k)))


def analyse(settings: Settings) -> Analysis:
    return Analysis(settings, A.run_all(settings.s, settings.m, settings.seed, settings.fill, C.BUDGETS[settings.budget]))


@lru_cache(maxsize=1)
def load_results() -> dict:
    return json.loads(RESULTS_PATH.read_text(encoding="utf-8"))


def _german(x: float, digits: int = 1) -> str:
    return f"{x:.{digits}f}".replace(".", ",")


def verdict_rounds(a: Analysis) -> tuple:
    """Kernfrage: Wie viele Runden ohne Wiederholung, und welches Verfahren schafft sie? Als (Art, Text); die App ruft st.<Art>(Text)."""
    r, m, s, b = a.results, a.settings.m, a.settings.s, a.bound
    con, sea, gre, zuf = r["konstruktion"], r["suche"], r["greedy"], r["zufall"]
    live = sea.available
    others = (f" Das Annealing findet {sea.value:.0f} Runden ({sea.stat}), der Greedy {_german(gre.value)} ({gre.stat}), zufällige Runden {_german(zuf.value)} ({zuf.stat})." if live
              else " Suche, Greedy und Zufall laufen hier nicht live (zu viele Personen), ihre Werte stehen in den Experimenten unten.")
    if con.available:
        kind = "success" if (not live or sea.value < m) else "info"
        return kind, (f"Die Körper-Konstruktion gibt **{m} Runden** ohne Wiederholung: jedes Paar aus verschiedenen Abteilungen sitzt genau einmal zusammen, "
                      f"mehr als {m} gehen bei {m} Tischen zu {s} nicht (Schranke)." + others)
    extra = ""
    if a.settings.fill:
        f = r["auffuellen"]
        extra = f" Mit zusätzlichem Tisch (Auffüllen und Streichen) gibt es **{f.value:.0f} Runden**, siehe unten."
    reason = con.note
    if live:
        return "info", (f"{reason} Das Annealing findet **{sea.value:.0f} Runden** von höchstens {b} (Schranke), der Greedy {_german(gre.value)} ({gre.stat}), "
                        f"zufällige Runden {_german(zuf.value)} ({zuf.stat}). Ob die Schranke von {b} erreichbar ist, entscheidet der Exakt-Tab (bis {C.EXACT_N_MAX} Personen)." + extra)
    return "info", f"{reason} Mehr als {C.N_LIVE_MAX} Personen: Suche, Greedy und Zufall laufen hier nicht live." + extra


def verdict_fill(a: Analysis) -> tuple:
    """Verdikt des Schalters „Zusätzliche Tische erlauben“."""
    f = a.results["auffuellen"]
    m, s = a.settings.m, a.settings.s
    if not f.available:
        return "info", "Der Schalter ist aus: es gelten genau m Tische zu s Personen. Eingeschaltet, erlaubt er mehr Tische und Tische mit weniger Personen."
    mt = f.metrics
    q = int(f.value)
    if q == m:
        return "info", f"Hier ist nichts aufzufüllen: m = {m} ist selbst die Größe eines Körpers, die Konstruktion hat schon {m} Runden."
    text = (f"Auffüllen und Streichen gibt **{q} Runden** ohne Wiederholung statt höchstens {a.bound} bei {m} Tischen zu {s}. Preis: {mt.tables_min} bis {mt.tables_max} Tische je Runde, "
            f"Tische mit {mt.size_min} bis {mt.size_max} Personen, {mt.singles} Einzelpersonen am Tisch (über alle Runden).")
    return ("success" if mt.singles == 0 else "warning"), text


def verdict_exact(status: str, s: int, m: int, w: int) -> tuple:
    """Verdikt des Exakt-Tabs. „Unentschieden“ ist kein Beweis der Unmöglichkeit."""
    if status == "ja":
        return "success", f"Es gibt {w} Runden ohne Wiederholung bei {m} Tischen zu {s} (Plan gefunden und geprüft)."
    if status == "unmöglich":
        return "error", f"Bewiesen: {w} Runden ohne Wiederholung gibt es bei {m} Tischen zu {s} nicht (CP-SAT, Modell wie in der README beschrieben)."
    return "warning", f"Nicht entschieden: CP-SAT hat im Zeitlimit weder einen Plan für {w} Runden gefunden noch ihre Unmöglichkeit bewiesen. Das ist kein Beweis, dass es keinen gibt."
