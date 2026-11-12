"""Orakel-Tests: unabhängige Rechenwege für Begegnungszähler, Konstruktion, Rundenzahl und Exakt-Löser (DEMO-PLAYBOOK §12).

* Begegnungen über die Inzidenzmatrix N·Nᵀ (numpy) statt über Paarschleifen.
* Maximale Rundenzahl kleiner Fälle durch vollständige Aufzählung aller Runden und Tiefensuche (ohne Körper, ohne CP-SAT, ohne Suche).
* CP-SAT-Modell ohne Symmetriebrechung gegen das Modell der Demo.
* Zufallsrunden: erwartete Abdeckung 1 − (1 − 1/m)^R."""

from itertools import combinations, permutations

import numpy as np
import pytest

import trt_check as K
import trt_designs as D
import trt_exact as X
import trt_rng as R
import trt_search as S


def _incidence_counts(plan, n):
    """Begegnungsmatrix aus der Inzidenzmatrix: je Runde N (Personen × Tische), Summe der N·Nᵀ, Diagonale null."""
    total = np.zeros((n, n), dtype=int)
    for rnd in plan:
        inc = np.zeros((n, len(rnd)), dtype=int)
        for t, table in enumerate(rnd):
            for p in table:
                inc[p, t] = 1
        total += inc @ inc.T
    np.fill_diagonal(total, 0)
    return total


def _plans():
    out = [("konstruktion", s, m, D.construction_plan(s, m)) for s, m in ((3, 4), (3, 5), (4, 5), (4, 7), (6, 8))]
    out += [("auffuellen", s, m, D.fill_plan(s, m)[1]) for s, m in ((3, 6), (6, 6), (4, 10), (3, 2))]
    out += [("greedy", s, m, S.greedy_rounds(s, m, 3)[0]) for s, m in ((3, 5), (4, 6))]
    out += [("zufall", s, m, S.random_rounds(s, m, 3)) for s, m in ((3, 5), (4, 6))]
    # ein Plan MIT Wiederholungen: Annealing mit zu wenig Budget
    out.append(("rest", 6, 8, S.anneal([], 5, 6, 8, R.SplitMix64(2), 5000)[0]))
    return out


@pytest.mark.parametrize("name,s,m,plan", _plans(), ids=lambda x: x if isinstance(x, str) else "")
def test_pruefer_stimmt_mit_der_inzidenzmatrix_ueberein(name, s, m, plan):
    n = s * m
    cnt = _incidence_counts(plan, n)
    dept = np.arange(n) // m
    cross = dept[:, None] != dept[None, :]
    mt = K.analyse_plan(plan, s, m)
    assert mt.repeats == int(np.triu(np.maximum(cnt - 1, 0), 1).sum())
    assert mt.same_dept == int(np.triu(np.where(cross, 0, cnt), 1).sum())
    assert mt.covered == int(np.triu(np.where(cross, cnt > 0, False), 1).sum())
    assert mt.cross_pairs == int(np.triu(cross, 1).sum())


@pytest.mark.parametrize("s,m", [(2, 2), (2, 3), (2, 4), (3, 4), (3, 5), (4, 5), (4, 7), (3, 8), (6, 8), (4, 9)])
def test_konstruktion_trifft_jedes_fremdpaar_genau_einmal(s, m):
    """Existenzsatz: Körper-Konstruktion hat m Runden, jedes Paar aus verschiedenen Abteilungen sitzt genau einmal zusammen, nie Paare derselben Abteilung."""
    n = s * m
    cnt = _incidence_counts(D.construction_plan(s, m), n)
    dept = np.arange(n) // m
    same = dept[:, None] == dept[None, :]
    assert (cnt[same] == 0).all() and (cnt[~same] == 1).all()


@pytest.mark.parametrize("s,m", [(3, 6), (4, 6), (5, 6), (6, 6), (3, 10), (4, 10), (3, 12), (6, 14)])
def test_auffuellen_trifft_jedes_fremdpaar_genau_einmal(s, m):
    q, plan = D.fill_plan(s, m)
    n = s * m
    cnt = _incidence_counts(plan, n)
    dept = np.arange(n) // m
    same = dept[:, None] == dept[None, :]
    assert len(plan) == q and (cnt[same] == 0).all() and (cnt[~same] == 1).all()
    assert all(sorted(p for t in rnd for p in t) == list(range(n)) for rnd in plan)


def _all_rounds(s, m):
    """Alle Runden (Abteilung 0 fest: Person i an Tisch i; Tische nicht unterscheidbar): für jede weitere Abteilung eine Permutation."""
    rounds = []
    for perms in _product([list(permutations(range(m)))] * (s - 1)):
        tables = [[i] + [d * m + perms[d - 1][i] for d in range(1, s)] for i in range(m)]
        rounds.append(tables)
    return rounds


def _product(lists):
    if not lists:
        yield ()
        return
    for x in lists[0]:
        for rest in _product(lists[1:]):
            yield (x,) + rest


def _max_rounds_brute_force(s, m):
    """Größte Zahl von Runden ohne Wiederholung durch Aufzählung aller Runden und Tiefensuche über paarweise paardisjunkte Runden."""
    rounds = _all_rounds(s, m)
    pairs = [frozenset(frozenset(p) for t in rnd for p in combinations(t, 2)) for rnd in rounds]
    best = 0

    def grow(start, used, count):
        nonlocal best
        best = max(best, count)
        for k in range(start, len(rounds)):
            if not (pairs[k] & used):
                grow(k + 1, used | pairs[k], count + 1)

    grow(0, frozenset(), 0)
    return best


# (s, m, größte Rundenzahl): 3×2 und 4×3 nur eine Runde (s > m: die s Personen eines Tisches passen nicht auf m < s Tische der nächsten Runde), sonst so viele wie Tische (Körper)
BRUTE = [(2, 2, 2), (2, 3, 3), (3, 2, 1), (3, 3, 3), (4, 3, 1), (3, 4, 4), (2, 4, 4)]


@pytest.mark.parametrize("s,m,expected", BRUTE)
def test_maximale_rundenzahl_kleiner_faelle_durch_aufzaehlung(s, m, expected):
    assert _max_rounds_brute_force(s, m) == expected


@pytest.mark.parametrize("s,m,expected", BRUTE)
def test_exakt_loeser_stimmt_mit_der_aufzaehlung_ueberein(s, m, expected):
    for w in range(1, m + 1):
        status, plan = X.exists_rounds(s, m, w, time_limit=20)
        assert status == ("ja" if w <= expected else "unmöglich"), (s, m, w)
        if status == "ja":
            assert K.analyse_plan(plan, s, m).repeats == 0


@pytest.mark.parametrize("s,m,expected", BRUTE)
def test_verfahren_ueberschreiten_die_aufzaehlung_nie_und_konstruktion_erreicht_sie(s, m, expected):
    assert len(S.greedy_rounds(s, m, 1)[0]) <= expected
    assert len(S.anneal_rounds(s, m, 1, 20000)[0]) <= expected
    assert len(S.random_rounds(s, m, 1)) <= expected
    if D.construction_available(s, m):
        assert len(D.construction_plan(s, m)) == expected


def _cpsat_without_symmetry_breaking(s, m, w):
    from ortools.sat.python import cp_model

    model = cp_model.CpModel()
    x = {(r, d, i, t): model.NewBoolVar("") for r in range(w) for d in range(s) for i in range(m) for t in range(m)}
    for r in range(w):
        for d in range(s):
            for i in range(m):
                model.AddExactlyOne(x[r, d, i, t] for t in range(m))
            for t in range(m):
                model.AddExactlyOne(x[r, d, i, t] for i in range(m))
    people = [(d, i) for d in range(s) for i in range(m)]
    for (d, i), (e, j) in combinations(people, 2):
        if d != e:
            met = []
            for r in range(w):
                v = model.NewBoolVar("")
                for t in range(m):
                    model.AddBoolOr([x[r, d, i, t].Not(), x[r, e, j, t].Not(), v])
                met.append(v)
            model.Add(sum(met) <= 1)
    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 2
    solver.parameters.max_time_in_seconds = 30
    return solver.StatusName(solver.Solve(model))


@pytest.mark.parametrize("s,m,w", [(3, 2, 2), (3, 3, 3), (4, 3, 3), (3, 4, 4), (3, 4, 3), (4, 4, 4)])
def test_symmetriebrechung_aendert_die_antwort_nicht(s, m, w):
    brechung = X.exists_rounds(s, m, w, time_limit=30)[0]
    ohne = _cpsat_without_symmetry_breaking(s, m, w)
    assert brechung == ("ja" if ohne in ("OPTIMAL", "FEASIBLE") else "unmöglich")


def test_euler_fall_3x6_fuenf_runden_ja_sechs_unmoeglich():
    """Tarry: zwei orthogonale lateinische Quadrate der Ordnung 6 gibt es nicht; 3 Abteilungen à 6 mit 6 Runden entspricht genau diesem Paar."""
    assert X.exists_rounds(3, 6, 5, time_limit=30)[0] == "ja"
    assert X.exists_rounds(3, 6, 6, time_limit=60, workers=4)[0] == "unmöglich"


def test_zufallsrunden_decken_im_mittel_1_minus_1_minus_1_durch_m_hoch_r_ab():
    """Jedes Fremdpaar sitzt in einer Zufallsrunde mit Wahrscheinlichkeit 1/m am selben Tisch (je Abteilung zufällige Zuordnung)."""
    s, m, trials = 4, 5, 400
    for rounds in (1, 2, 3, 5):
        values = []
        for seed in range(trials):
            rng = R.SplitMix64(1000 + seed)
            plan = [S.random_round(s, m, rng) for _ in range(rounds)]
            values.append(K.analyse_plan(plan, s, m).coverage)
        expected = 1 - (1 - 1 / m) ** rounds
        assert abs(np.mean(values) - expected) < 0.02, (rounds, np.mean(values), expected)
