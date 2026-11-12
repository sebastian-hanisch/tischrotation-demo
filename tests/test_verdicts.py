"""Verdikte als reine Funktionen: Schwellen und jede Zahl im Text an handgesetzten Werten; dazu das Verdikt jedes Presets."""

import pytest

import trt_algorithm as A
import trt_constants as C
import trt_evaluation as ev
from trt_check import PlanMetrics


def _mt(rounds=3, singles=0, size=(3, 3), tables=(4, 4)):
    return PlanMetrics(rounds, 0, 0, 100, 100, singles, size[0], size[1], tables[0], tables[1], True)


def _mr(key, value, available=True, note="", stat="ein Lauf", metrics=None):
    if not available:
        return A.MethodResult(key, False, 0.0, "", (), None, note)
    return A.MethodResult(key, True, float(value), stat, (), metrics or _mt(int(value)), note)


def _analysis(s, m, cons=None, fill=None, sea=3, gre=3.0, zuf=1.0, live=True, fill_on=False, cons_note="keine Konstruktion"):
    res = {
        "konstruktion": _mr("konstruktion", cons) if cons else _mr("konstruktion", 0, False, cons_note),
        "auffuellen": fill if fill else _mr("auffuellen", 0, False, "aus"),
        "suche": _mr("suche", sea) if live else _mr("suche", 0, False, "zu groß"),
        "greedy": _mr("greedy", gre, stat="Median über 5 Zufalls-Seeds") if live else _mr("greedy", 0, False, "zu groß"),
        "zufall": _mr("zufall", zuf, stat="Mittel über 200 Zufallsfolgen") if live else _mr("zufall", 0, False, "zu groß"),
    }
    return ev.Analysis(ev.Settings(s, m, 1, fill_on), res)


def test_verdikt_konstruktion_schlaegt_suche():
    kind, text = ev.verdict_rounds(_analysis(6, 8, cons=8, sea=3, gre=3.0, zuf=1.0))
    assert kind == "success"
    assert "**8 Runden**" in text and "mehr als 8 gehen bei 8 Tischen zu 6 nicht" in text
    assert "Das Annealing findet 3 Runden (ein Lauf), der Greedy 3,0 (Median über 5 Zufalls-Seeds), zufällige Runden 1,0 (Mittel über 200 Zufallsfolgen)" in text


def test_verdikt_wenn_die_suche_die_schranke_erreicht_ist_nur_info():
    kind, text = ev.verdict_rounds(_analysis(3, 5, cons=5, sea=5, gre=3.0, zuf=1.1))
    assert kind == "info" and "**5 Runden**" in text and "Das Annealing findet 5 Runden" in text


def test_verdikt_ohne_live_suche_nennt_die_experimente():
    kind, text = ev.verdict_rounds(_analysis(6, 8, cons=8, live=False))
    assert kind == "success" and "laufen hier nicht live" in text and "Annealing findet" not in text


def test_verdikt_ohne_konstruktion_verweist_auf_den_exakt_tab():
    kind, text = ev.verdict_rounds(_analysis(3, 6, sea=5, gre=4.0, zuf=1.06, cons_note="m = 6 ist keine Primzahlpotenz: die Körper-Konstruktion braucht einen Körper mit m Elementen."))
    assert kind == "info" and text.startswith("m = 6 ist keine Primzahlpotenz")
    assert "**5 Runden** von höchstens 6 (Schranke)" in text and "Exakt-Tab (bis 24 Personen)" in text and "zusätzlichem Tisch" not in text


def test_verdikt_ohne_konstruktion_mit_auffuellen_nennt_die_rundenzahl():
    fill = _mr("auffuellen", 7, note="q = 7", metrics=_mt(7, size=(2, 3), tables=(6, 7)))
    kind, text = ev.verdict_rounds(_analysis(3, 6, fill=fill, fill_on=True, sea=5, gre=4.0))
    assert kind == "info" and "Mit zusätzlichem Tisch (Auffüllen und Streichen) gibt es **7 Runden**" in text


def test_verdikt_ohne_live_und_ohne_konstruktion():
    kind, text = ev.verdict_rounds(_analysis(8, 12, live=False))
    assert kind == "info" and "Mehr als 60 Personen" in text


def test_verdikt_bei_mehr_abteilungen_als_personen_nennt_die_schranke_1():
    a = _analysis(4, 3, sea=1, gre=1.0, zuf=1.0, cons_note="s = 4 Abteilungen sind mehr als m = 3 Personen je Abteilung")
    kind, text = ev.verdict_rounds(a)
    assert a.bound == 1 and kind == "info" and "von höchstens 1 (Schranke)" in text


def test_verdikt_auffuellen_aus_gleich_und_mit_einzelpersonen():
    kind, text = ev.verdict_fill(_analysis(6, 8, cons=8))
    assert kind == "info" and "Der Schalter ist aus" in text
    fill = _mr("auffuellen", 7, metrics=_mt(7, size=(5, 6), tables=(6, 7)))
    kind, text = ev.verdict_fill(_analysis(6, 6, fill=fill, fill_on=True))
    assert kind == "success"
    assert "**7 Runden** ohne Wiederholung statt höchstens 6 bei 6 Tischen zu 6" in text and "6 bis 7 Tische je Runde, Tische mit 5 bis 6 Personen, 0 Einzelpersonen" in text
    fill = _mr("auffuellen", 11, metrics=_mt(11, singles=48, size=(1, 3), tables=(10, 11)))
    kind, text = ev.verdict_fill(_analysis(3, 10, fill=fill, fill_on=True))
    assert kind == "warning" and "48 Einzelpersonen" in text
    kind, text = ev.verdict_fill(_analysis(6, 8, fill=_mr("auffuellen", 8, metrics=_mt(8)), fill_on=True))
    assert kind == "info" and "nichts aufzufüllen" in text


def test_verdikt_exakt():
    assert ev.verdict_exact("ja", 3, 5, 5) == ("success", "Es gibt 5 Runden ohne Wiederholung bei 5 Tischen zu 3 (Plan gefunden und geprüft).")
    kind, text = ev.verdict_exact("unmöglich", 3, 6, 6)
    assert kind == "error" and "Bewiesen: 6 Runden" in text
    kind, text = ev.verdict_exact("unentschieden", 3, 6, 6)
    assert kind == "warning" and "kein Beweis" in text


def test_best_key_nimmt_die_meisten_runden_und_bei_gleichstand_die_konstruktion():
    assert _analysis(6, 8, cons=8, sea=3).best_key() == "konstruktion"
    assert _analysis(3, 5, cons=5, sea=5).best_key() == "konstruktion"
    assert _analysis(3, 6, sea=5).best_key() == "suche"
    assert _analysis(8, 12, live=False).best_key() is None


EXPECTED_KIND = {"Firmenfeier 48": "success", "Euler-Fall 18": "info", "Auffüllen 36": "info", "Mittlere Feier 40": "info", "Kleine Feier 15": "info"}


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_jedes_preset_zeigt_das_erwartete_verdikt(name):
    a = ev.analyse(ev.Settings(**C.PRESETS[name]))
    kind, text = ev.verdict_rounds(a)
    assert kind == EXPECTED_KIND[name], text
    if C.PRESETS[name]["fill"]:
        assert ev.verdict_fill(a)[0] == "success"
    assert "Schranke" in text


def test_preset_euler_fall_nennt_kein_unmoeglich_ohne_beweis():
    a = ev.analyse(ev.Settings(**C.PRESETS["Euler-Fall 18"]))
    _kind, text = ev.verdict_rounds(a)
    assert "unmöglich" not in text and "Exakt-Tab" in text
