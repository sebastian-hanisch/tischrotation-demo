"""Randfälle: kleinste Feiern, mehr Abteilungen als Personen je Abteilung, Grenzen der Regler, Auffüllen ohne Wirkung."""

import pytest

import trt_algorithm as A
import trt_check as K
import trt_constants as C
import trt_designs as D
import trt_exact as X
import trt_search as S


def test_kleinste_feier_2x2():
    assert len(D.construction_plan(2, 2)) == 2
    plan, why = S.greedy_rounds(2, 2, 1)
    assert len(plan) == 2 and why == "alle"
    plan, _ = S.anneal_rounds(2, 2, 1, 1000)
    assert len(plan) == 2


def test_zwei_personen_je_abteilung_aber_drei_abteilungen_hat_nur_eine_runde():
    """3 Abteilungen à 2: nach der ersten Runde {a0,b0,c0} {a1,b1,c1} gibt jede zweite Runde eine Wiederholung (Aufzählung im Orakel-Test)."""
    assert len(S.greedy_rounds(3, 2, 1)[0]) == 1
    assert X.exists_rounds(3, 2, 2)[0] == "unmöglich" and X.exists_rounds(3, 2, 1)[0] == "ja"
    assert not D.construction_available(3, 2)


def test_mehr_runden_als_m_sind_unmoeglich():
    assert X.exists_rounds(3, 4, 5)[0] == "unmöglich"


def test_auffuellen_ohne_wirkung_wenn_m_ein_koerper_ist():
    for s, m in ((3, 4), (4, 5), (6, 8), (2, 2)):
        q, plan = D.fill_plan(s, m)
        assert q == m and plan == D.construction_plan(s, m)


def test_auffuellen_bei_mehr_abteilungen_als_personen():
    """6 Abteilungen à 3: q = 7 (nächste Körpergröße ≥ 6), also 7 Runden bei 3 bis 7 Tischen; keine Wiederholung."""
    q, plan = D.fill_plan(6, 3)
    mt = K.analyse_plan(plan, 6, 3)
    assert q == 7 and mt.rounds == 7 and mt.repeats == 0 and mt.same_dept == 0 and mt.coverage == 1.0 and mt.partition_ok


def test_auffuellen_an_den_reglergrenzen():
    for s in (C.S_MIN, C.S_MAX):
        for m in (C.M_MIN, C.M_MAX):
            q, plan = D.fill_plan(s, m)
            mt = K.analyse_plan(plan, s, m)
            assert mt.rounds == q >= max(s, m) and mt.repeats == 0 and mt.same_dept == 0 and mt.partition_ok and mt.coverage == 1.0


def test_run_all_ueber_der_live_grenze_laesst_suche_aus():
    out = A.run_all(8, 12, 1, True, 1000)
    assert out["konstruktion"].available is False  # 12 ist kein Körper
    assert out["auffuellen"].available and out["auffuellen"].value == 13
    assert not (out["suche"].available or out["greedy"].available or out["zufall"].available)


def test_run_all_ohne_auffuellen_markiert_es_als_nicht_verfuegbar():
    out = A.run_all(3, 4, 1, False, 100_000)
    assert out["auffuellen"].available is False and out["konstruktion"].value == 4 and out["suche"].available


def test_pruefer_bei_leerem_plan():
    mt = K.analyse_plan([], 3, 2)
    assert mt.rounds == 0 and mt.repeats == 0 and mt.coverage == 0.0 and mt.partition_ok
