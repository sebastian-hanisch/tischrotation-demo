"""Zahlen der README und der App: jede Aussage der Tabelle „Ergebnis“ wird hier über das GANZE Raster gezählt (DEMO-PLAYBOOK §11a).

Die vorgerechneten Messreihen stehen in data/trt_results.json (tools/make_results.py, feste Zufalls-Seeds). Schnelle Zeilen rechnen diese Tests neu;
die langen Läufe (30 Mio. Züge) sind eine Messung der README und werden nur gegen die Datei gelesen."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import make_results as M  # noqa: E402
import trt_designs as D  # noqa: E402
import trt_evaluation as ev  # noqa: E402
import trt_exact as X  # noqa: E402
from trt_check import analyse_plan  # noqa: E402

DATA = json.loads((ROOT / "data" / "trt_results.json").read_text(encoding="utf-8"))


def _row(s, m):
    return next(r for r in DATA["runden"] if (r["s"], r["m"]) == (s, m))


def test_die_messreihe_hat_14_groessen_mit_5_zufalls_seeds():
    assert len(DATA["runden"]) == 14 and DATA["meta"]["sweep_seeds"] == [100000, 100001, 100002, 100003, 100004]
    assert DATA["meta"]["sa_iters"] == 3_000_000 and DATA["meta"]["greedy_seeds"] == 5 and DATA["meta"]["random_trials"] == 200


def test_konstruktion_hat_in_8_von_14_groessen_m_runden_und_in_6_keine():
    """Konstruktion (m Primzahlpotenz, s ≤ m): 8 Größen mit genau m Runden und jedem Fremdpaar genau einmal; in 6 Größen (m = 6 oder 10) gibt es keine."""
    with_cons = [r for r in DATA["runden"] if r["konstruktion"]]
    without = [r for r in DATA["runden"] if not r["konstruktion"]]
    assert len(with_cons) == 8 and len(without) == 6 and {r["m"] for r in without} == {6, 10}
    for r in with_cons:
        plan = D.construction_plan(r["s"], r["m"])
        mt = analyse_plan(plan, r["s"], r["m"])
        assert r["konstruktion"] == r["schranke"] == len(plan) == r["m"]
        assert (mt.repeats, mt.same_dept, mt.coverage) == (0, 0, 1.0)


def test_annealing_liegt_in_5_von_8_groessen_mit_konstruktion_unter_der_konstruktion():
    cons = [r for r in DATA["runden"] if r["konstruktion"]]
    below = [(r["s"], r["m"]) for r in cons if r["suche_median"] < r["konstruktion"]]
    assert len(below) == 5 and set(below) == {(3, 7), (4, 7), (4, 8), (6, 7), (6, 8)}
    assert [(_row(6, 8)["suche_median"], _row(6, 8)["konstruktion"]), (_row(6, 7)["suche_median"], _row(6, 7)["konstruktion"])] == [(3, 8), (3, 7)]
    assert all(r["suche_median"] == r["konstruktion"] for r in cons if (r["s"], r["m"]) not in below)  # in den übrigen 3 Größen erreicht es sie (Median)


def test_annealing_erreicht_in_der_messreihe_nie_die_schranke_bei_m_gleich_6_oder_10():
    """Ohne Konstruktion (6 Größen): Median des Annealings unter der Schranke m in 6 von 6 Größen."""
    rows = [r for r in DATA["runden"] if not r["konstruktion"]]
    assert len(rows) == 6 and all(r["suche_median"] < r["schranke"] for r in rows)


def test_greedy_median_liegt_nie_ueber_dem_annealing_in_12_von_14_darunter_in_2_gleich():
    rows = DATA["runden"]
    assert all(r["greedy_median"] <= r["suche_median"] for r in rows)
    assert sum(1 for r in rows if r["greedy_median"] < r["suche_median"]) == 12
    assert {(r["s"], r["m"]) for r in rows if r["greedy_median"] == r["suche_median"]} == {(6, 6), (6, 8)}


def test_greedy_endet_nur_in_drei_groessen_am_knotenlimit():
    """Von je 25 Läufen (5 Zufalls-Seeds × 5 Unter-Seeds) endet der Greedy in 6×7, 6×8 und 4×10 am Knotenlimit, sonst nie vollständig durchsucht abgebrochen."""
    limits = {(r["s"], r["m"]): r["greedy_limit"] for r in DATA["runden"] if r["greedy_limit"]}
    assert limits == {(6, 7): 24, (6, 8): 25, (4, 10): 17}


def test_zufallsrunden_geben_im_mittel_hoechstens_1_05_runden():
    assert all(r["s"] >= 3 for r in DATA["runden"])
    assert max(r["zufall_mittel"] for r in DATA["runden"]) <= 1.05 and min(r["zufall_mittel"] for r in DATA["runden"]) >= 1.0


def test_zufall_bei_zwei_abteilungen_ist_haeufiger_wiederholungsfrei():
    """Bei s = 2 bleibt die zweite Runde in 25 bis 55 % der Folgen wiederholungsfrei (400 Folgen je Größe), die Wiederholung ist also nicht „fast immer“."""
    import trt_search as S

    for m in (2, 3, 5, 8, 12):
        runs = [len(S.random_rounds(2, m, 100000 * 1000 + k)) for k in range(400)]
        free = sum(1 for x in runs if x >= 2) / 400
        assert 0.25 <= free <= 0.55 and sum(runs) / 400 > 1.3, (m, free)


def test_unter_seeds_benachbarter_zufalls_seeds_ueberlappen_nicht():
    import trt_constants as C

    seeds = DATA["meta"]["sweep_seeds"]
    random_sets = [{s * C.SUBSEED_STRIDE + k for k in range(C.RANDOM_TRIALS)} for s in seeds]
    greedy_sets = [{s * C.SUBSEED_STRIDE + k for k in range(C.GREEDY_SEEDS)} for s in seeds]
    assert len(set().union(*random_sets)) == 5 * C.RANDOM_TRIALS == 1000 and len(set().union(*greedy_sets)) == 5 * C.GREEDY_SEEDS == 25


def test_annealing_erreicht_die_schranke_nur_in_kleinen_groessen():
    rows = {(r["s"], r["m"]): r for r in DATA["runden"]}
    assert [rows[k]["suche_bei_schranke"] for k in ((3, 4), (3, 5), (4, 5))] == [5, 5, 4]
    assert all(r["suche_bei_schranke"] == 0 for r in DATA["runden"] if r["konstruktion"] and r["s"] * r["m"] > 20)  # ab 21 Personen mit Konstruktion in 0 von 5 Zufalls-Seeds


def test_teilplan_aus_drei_abteilungen_ist_zulaessig():
    """Weglassen von Abteilungen erhält die Wiederholungsfreiheit: ein Plan für 4 Abteilungen zu 6 gibt einen für 3 Abteilungen zu 6, also ist die Schranke 6 für m = 6 und s ≥ 3 wie bei 3×6 unerreichbar."""
    import trt_search as S

    plan, _log = S.anneal_rounds(4, 6, 1, 200000)
    assert len(plan) >= 3
    restricted = [[[p for p in table if p // 6 < 3] for table in rnd] for rnd in plan]
    mt = analyse_plan(restricted, 3, 6)
    assert (mt.repeats, mt.same_dept, mt.partition_ok, mt.rounds) == (0, 0, True, len(plan))


def test_einzelpersonen_beim_auffuellen_auch_bei_gleich_grossen_abteilungen():
    assert {(s, m): analyse_plan(D.fill_plan(s, m)[1], s, m).singles for s, m in ((2, 6), (2, 10), (2, 12), (6, 2))} == {(2, 6): 12, (2, 10): 20, (2, 12): 24, (6, 2): 12}


@pytest.mark.parametrize("s,m", [(3, 4), (3, 5), (4, 5)])
def test_schnelle_zeilen_der_messreihe_lassen_sich_neu_rechnen(s, m):
    """Annealing, Greedy und Zufall mit denselben Zufalls-Seeds geben dieselben Zahlen wie die Datei."""
    raw = [M.runden_job((s, m, seed)) for seed in DATA["meta"]["sweep_seeds"]]
    row = _row(s, m)
    assert sorted(x["suche"] for x in raw)[2] == row["suche_median"]
    assert min(x["suche"] for x in raw) == row["suche_min"] and max(x["suche"] for x in raw) == row["suche_max"]
    assert sorted(x["greedy"] for x in raw)[2] == row["greedy_median"]
    assert abs(sum(x["zufall"] for x in raw) / 5 - row["zufall_mittel"]) < 1e-12
    assert sum(1 for x in raw if x["suche"] == m) == row["suche_bei_schranke"] and sum(x["greedy_limit"] for x in raw) == row["greedy_limit"]


def test_euler_tabelle_stimmt_mit_dem_loeser_ueberein():
    expected = {(3, 2, 2): "unmöglich", (3, 3, 3): "ja", (3, 4, 4): "ja", (3, 5, 5): "ja", (3, 6, 5): "ja", (3, 6, 6): "unmöglich"}
    assert {(e["s"], e["m"], e["w"]): e["status"] for e in DATA["euler"]} == expected
    for (s, m, w), status in expected.items():
        assert X.exists_rounds(s, m, w, time_limit=60, workers=4)[0] == status


def test_auffuellen_gibt_in_10_von_10_groessen_q_runden_ohne_wiederholung_und_ohne_einzelpersonen():
    rows = DATA["auffuellen"]
    assert len(rows) == 10
    for r in rows:
        q, plan = D.fill_plan(r["s"], r["m"])
        mt = analyse_plan(plan, r["s"], r["m"])
        assert (r["q"], r["runden"]) == (q, len(plan)) and q > r["m"]
        assert (mt.repeats, mt.same_dept, mt.coverage, mt.singles, mt.partition_ok) == (0, 0, 1.0, 0, True)
        assert (r["size_min"], r["size_max"], r["tables_min"], r["tables_max"]) == (mt.size_min, mt.size_max, mt.tables_min, mt.tables_max)
        assert r["s"] - (q - r["m"]) <= r["size_min"] <= r["size_max"] <= r["s"]  # je gestrichener Person je Abteilung fehlt am Tisch höchstens eine
    assert sum(r["singles"] for r in rows) == 0


def test_auffuellen_liegt_in_10_von_10_groessen_ueber_dem_annealing_und_ueber_der_schranke():
    rows = DATA["auffuellen"]
    assert all(r["runden"] > r["suche_median"] and r["runden"] > r["m"] for r in rows)
    assert {(r["s"], r["m"]): r["runden"] for r in rows}[(3, 6)] == 7 and {(r["s"], r["m"]): r["suche_median"] for r in rows}[(3, 6)] == 5


def test_zufallsabdeckung_folgt_der_formel_1_minus_1_minus_1_durch_m_hoch_r():
    ab = DATA["abdeckung"]
    assert (ab["s"], ab["m"], ab["folgen"]) == (4, 5, 2000)
    for r in ab["rows"]:
        assert abs(r["zufall"] - r["formel"]) < 0.01 and r["konstruktion"] == pytest.approx(r["R"] / ab["m"])
        assert r["konstruktion"] >= r["zufall"] - 1e-9
    assert ab["rows"][-1]["konstruktion"] == 1.0 and abs(ab["rows"][-1]["zufall"] - 0.672) < 0.01


def test_rechenbudget_30_mio_zuege_lassen_mindestens_eine_wiederholung_uebrig():
    bu = DATA["budget"]
    assert (bu["s"], bu["m"], bu["w"]) == (6, 8, 4)
    assert [sum(r["rest"]) for r in bu["rows"]] == [7, 6, 4]  # die Summe über die 3 Zufalls-Seeds sinkt: etwas Wirkung, aber keine Lösung
    assert [r["rest_min"] for r in bu["rows"]] == [2, 2, 1] and [r["budget"] for r in bu["rows"]] == [300_000, 3_000_000, 30_000_000]
    assert all(min(r["rest"]) >= 1 for r in bu["rows"])  # in 9 von 9 Läufen bleibt mindestens eine übrig
    first = M.budget_job((6, 8, 4, 300_000, 100000))  # die kürzeste Zeile lässt sich neu rechnen; 3 und 30 Mio. Züge sind Messungen der README
    assert first["rest"] == bu["rows"][0]["rest"][0]


def test_bei_mehr_abteilungen_als_personen_je_abteilung_gibt_es_nur_eine_runde():
    """s > m: die s Personen eines Tisches müssten sich in der nächsten Runde auf m < s Tische verteilen (Taubenschlag). Der Löser beweist es für zwei Größen."""
    assert ev.Analysis(ev.Settings(4, 3), {}).bound == 1 and ev.Analysis(ev.Settings(3, 3), {}).bound == 3
    for s, m in ((4, 3), (5, 4)):
        assert X.exists_rounds(s, m, 1)[0] == "ja" and X.exists_rounds(s, m, 2)[0] == "unmöglich"
