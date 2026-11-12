"""Kern gegen Handrechnung: Körper, Konstruktion, Auffüllen, Prüfer, Suchverfahren."""

import pytest

import trt_check as K
import trt_designs as D
import trt_field as F
import trt_rng as R
import trt_search as S


def test_splitmix64_erste_werte_sind_die_der_referenz():
    """Referenzwerte der veröffentlichten SplitMix64-Implementierung (Vigna) für den Zustand 0."""
    rng = R.SplitMix64(0)
    assert [rng.next_u64() for _ in range(2)] == [0xE220A8397B1DCDAF, 0x6E789E6AA1B965F4]


def test_zufallsfolge_ist_fuer_gleichen_seed_gleich_und_fuer_andere_verschieden():
    a, b, c = R.SplitMix64(7), R.SplitMix64(7), R.SplitMix64(8)
    fa = [a.below(1000) for _ in range(20)]
    assert fa == [b.below(1000) for _ in range(20)]
    assert fa != [c.below(1000) for _ in range(20)]


def test_shuffle_ist_eine_permutation():
    items = list(range(30))
    R.SplitMix64(3).shuffle(items)
    assert sorted(items) == list(range(30)) and items != list(range(30))


def test_gf4_von_hand():
    """GF(4) = {0, 1, a, a+1} mit a² = a + 1, kodiert als 0, 1, 2, 3. Addition ist XOR; a·a = a+1 (3), a·(a+1) = a²+a = 1, (a+1)² = a²+1 = a (2)."""
    f = F.GF(4)
    assert f.add[2][3] == 1 and f.add[1][2] == 3 and f.add[3][3] == 0
    assert f.mul[2][2] == 3 and f.mul[2][3] == 1 and f.mul[3][3] == 2 and f.mul[1][3] == 3


@pytest.mark.parametrize("q", [2, 3, 4, 5, 7, 8, 9, 11, 13, 16, 25, 27])
def test_jeder_koerper_hat_inverse_und_distributivgesetz(q):
    f = F.GF(q)
    for a in range(1, q):
        assert sum(1 for b in range(1, q) if f.mul[a][b] == 1) == 1  # genau ein Inverses
    for a in range(0, q, max(1, q // 5)):
        for b in range(q):
            for c in range(q):
                assert f.mul[a][f.add[b][c]] == f.add[f.mul[a][b]][f.mul[a][c]]


def test_primzahlpotenzen():
    assert [q for q in range(2, 20) if F.is_prime_power(q)] == [2, 3, 4, 5, 7, 8, 9, 11, 13, 16, 17, 19]
    with pytest.raises(ValueError):
        F.GF(6)


def test_naechste_primzahlpotenz():
    assert [D.next_prime_power(x) for x in (1, 2, 6, 10, 12, 14, 15, 17)] == [2, 2, 7, 11, 13, 16, 16, 17]


def test_konstruktion_2x2_von_hand():
    """s = 2 Abteilungen à 2 aus GF(2): Runde 0: {0,2} {1,3}; Runde 1: {0,3} {1,2} (Person i der Abteilung d an Tisch t + r·d)."""
    assert D.construction_plan(2, 2) == [[[0, 2], [1, 3]], [[0, 3], [1, 2]]]


def test_auffuellen_3x2_von_hand(mini_plan):
    q, plan = D.fill_plan(3, 2)
    assert q == 3 and plan == mini_plan


def test_pruefer_an_der_mini_instanz(mini_plan):
    mt = K.analyse_plan(mini_plan, 3, 2)
    assert (mt.rounds, mt.repeats, mt.same_dept, mt.cross_pairs, mt.covered, mt.singles) == (3, 0, 0, 12, 12, 0)
    assert (mt.size_min, mt.size_max, mt.tables_min, mt.tables_max, mt.partition_ok) == (2, 3, 2, 3, True)
    assert mt.coverage == 1.0


def test_pruefer_findet_wiederholung_und_gleiche_abteilung():
    plan = [[[0, 2], [1, 3]], [[0, 2], [1, 3]]]  # (0,2) und (1,3) sitzen zweimal zusammen
    mt = K.analyse_plan(plan, 2, 2)
    assert mt.repeats == 2 and mt.covered == 2 and mt.same_dept == 0
    assert K.analyse_plan([[[0, 1], [2, 3]]], 2, 2).same_dept == 2  # Paare 0/1 und 2/3 gehören je zu einer Abteilung


def test_wiederholungsfreies_praefix():
    plan = [[[0, 1], [2, 3]], [[0, 2], [1, 3]], [[0, 1], [2, 3]]]
    assert K.repeat_free_prefix(plan, 4) == 2
    assert K.repeat_free_prefix(plan[:2], 4) == 2 and K.repeat_free_prefix([], 4) == 0


def test_zufallsrunde_ist_gueltig():
    rnd = S.random_round(4, 5, R.SplitMix64(1))
    assert sorted(p for t in rnd for p in t) == list(range(20))
    assert all([p // 5 for p in table] == [0, 1, 2, 3] for table in rnd)  # an Stelle d steht die Person der Abteilung d


def test_zufallsrunden_enden_vor_der_ersten_wiederholung():
    plan = S.random_rounds(3, 4, 11)
    assert 1 <= len(plan) <= 4
    assert K.repeat_free_prefix(plan, 12) == len(plan)


def test_greedy_plan_ist_wiederholungsfrei_und_gueltig():
    plan, why = S.greedy_rounds(3, 5, 1)
    mt = K.analyse_plan(plan, 3, 5)
    assert mt.repeats == 0 and mt.same_dept == 0 and mt.partition_ok and why in ("vollständig", "Knotenlimit", "alle")
    assert S.greedy_rounds(3, 5, 1)[0] == plan  # reproduzierbar


def test_annealing_findet_die_schranke_bei_3x5_und_ist_reproduzierbar():
    plan, log = S.anneal_rounds(3, 5, 1, 1_000_000)
    assert len(plan) == 5 and K.analyse_plan(plan, 3, 5).repeats == 0
    assert S.anneal_rounds(3, 5, 1, 1_000_000)[0] == plan
    assert log[0] == (1, 0, 0)


def test_annealing_kosten_stimmen_mit_dem_pruefer_ueberein():
    """Der Restwert einer gescheiterten Rundenzahl ist die Zahl überzähliger Begegnungen im besten Plan (nicht nur eine Schätzung im Lauf)."""
    rng = R.SplitMix64(5)
    plan, cost, _moves = S.anneal([], 4, 6, 8, rng, 20000)  # 6 Abteilungen à 8, 4 Runden, kurzes Budget: bleibt ein Rest
    assert cost == K.analyse_plan(plan, 6, 8).repeats and cost > 0
    assert K.analyse_plan(plan, 6, 8).same_dept == 0 and K.analyse_plan(plan, 6, 8).partition_ok


def test_konstruktion_nicht_verfuegbar_fuer_nichtkoerper_und_zu_viele_abteilungen():
    assert not D.construction_available(3, 6) and not D.construction_available(4, 3) and D.construction_available(3, 3)
    with pytest.raises(ValueError):
        D.construction_plan(3, 6)
    with pytest.raises(ValueError):
        D.transversal_rounds(4, 3)
