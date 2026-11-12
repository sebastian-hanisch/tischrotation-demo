"""Vorgerechnete Messreihen der Demo (data/trt_results.json). Aufruf aus dem Demo-Ordner:  python tools/make_results.py [runden|euler|abdeckung|budget|auffuellen|alle]

Alle Läufe mit festen Zufalls-Seeds (C.SWEEP_SEEDS), reproduzierbar mit dem eigenen SplitMix64. Rohdaten je Lauf liegen in tools/raw/.
Die Tests rechnen die schnellen Zeilen neu und prüfen jede Zahl der README gegen diese Datei (tests/test_claims.py)."""

import json
import sys
from multiprocessing import Pool
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import trt_algorithm as A  # noqa: E402
import trt_constants as C  # noqa: E402
import trt_designs as D  # noqa: E402
import trt_exact as X  # noqa: E402
import trt_search as S  # noqa: E402
from trt_check import analyse_plan  # noqa: E402
from trt_rng import SplitMix64  # noqa: E402

RUNDEN_CASES = [(3, 4), (3, 5), (3, 6), (3, 7), (4, 5), (4, 6), (4, 7), (4, 8), (5, 6), (6, 6), (6, 7), (6, 8), (3, 10), (4, 10)]
EULER_CASES = [(3, 2, 2), (3, 3, 3), (3, 4, 4), (3, 5, 5), (3, 6, 5), (3, 6, 6)]
FILL_CASES = [(3, 6), (4, 6), (5, 6), (6, 6), (3, 10), (4, 10), (6, 10), (3, 12), (4, 12), (6, 14)]
ABDECKUNG = (4, 5)  # s, m
BUDGET_CASE = (6, 8, 4)  # s, m, w
BUDGETS = (300_000, 3_000_000, 30_000_000)
SA_ITERS = 3_000_000


def runden_job(args):
    s, m, seed = args
    sa = A.search_result(s, m, seed, SA_ITERS)
    gr = A.greedy_result(s, m, seed)
    zu = A.random_result(s, m, seed)
    reasons = [S.greedy_rounds(s, m, seed * C.SUBSEED_STRIDE + k, C.NODE_LIMIT)[1] for k in range(C.GREEDY_SEEDS)]
    return dict(s=s, m=m, seed=seed, suche=int(sa.value), greedy=gr.value, zufall=zu.value, greedy_limit=sum(1 for w in reasons if w == "Knotenlimit"))


def part_runden(pool):
    jobs = [(s, m, seed) for (s, m) in RUNDEN_CASES for seed in C.SWEEP_SEEDS]
    raw = list(pool.imap(runden_job, jobs))
    rows = []
    for (s, m) in RUNDEN_CASES:
        r = [x for x in raw if x["s"] == s and x["m"] == m]
        cons = A.construction_result(s, m)
        rows.append(dict(
            s=s, m=m, n=s * m, schranke=m,
            konstruktion=int(cons.value) if cons.available else None,
            suche_median=median(x["suche"] for x in r), suche_min=min(x["suche"] for x in r), suche_max=max(x["suche"] for x in r),
            greedy_median=median(x["greedy"] for x in r), greedy_min=min(x["greedy"] for x in r), greedy_max=max(x["greedy"] for x in r),
            zufall_mittel=mean(x["zufall"] for x in r),
            suche_bei_schranke=sum(1 for x in r if x["suche"] == m), greedy_limit=sum(x["greedy_limit"] for x in r),
        ))
    return rows, raw


def part_euler():
    rows = []
    for s, m, w in EULER_CASES:
        status, _ = X.exists_rounds(s, m, w, time_limit=120.0, workers=4)
        rows.append(dict(s=s, m=m, w=w, status=status))
    return rows


def abdeckung_job(seed):
    s, m = ABDECKUNG
    rng = SplitMix64(seed)
    n = s * m
    out = []
    plan = []
    for r in range(1, m + 1):
        plan.append(S.random_round(s, m, rng))
        out.append(analyse_plan(plan, s, m).coverage)
    return out


def part_abdeckung():
    s, m = ABDECKUNG
    seeds = list(range(100000, 100000 + 2000))
    runs = [abdeckung_job(seed) for seed in seeds]
    rows = []
    cons = D.construction_plan(s, m)
    for r in range(1, m + 1):
        rows.append(dict(R=r, zufall=mean(run[r - 1] for run in runs), konstruktion=analyse_plan(cons[:r], s, m).coverage,
                         formel=1 - (1 - 1 / m) ** r))
    return dict(s=s, m=m, folgen=len(seeds), rows=rows)


def budget_job(args):
    s, m, w, budget, seed = args
    rng = SplitMix64(seed)
    plan = []
    for k in range(1, w):  # Runden 1..w-1 wie in der Suche aufbauen (3 Mio. Züge je Runde), dann w mit dem untersuchten Budget
        best, cost, _ = S.anneal(plan, k, s, m, rng, SA_ITERS)
        if cost > 0:
            return dict(budget=budget, seed=seed, rest=None)
        plan = best
    best, cost, moves = S.anneal(plan, w, s, m, rng, budget)
    return dict(budget=budget, seed=seed, rest=cost, moves=moves)


def part_budget(pool):
    s, m, w = BUDGET_CASE
    jobs = [(s, m, w, b, seed) for b in BUDGETS for seed in C.SWEEP_SEEDS[:3]]
    raw = list(pool.imap(budget_job, jobs))
    rows = []
    for b in BUDGETS:
        r = [x for x in raw if x["budget"] == b]
        rows.append(dict(budget=b, rest=[x["rest"] for x in r], rest_min=min(x["rest"] for x in r if x["rest"] is not None)))
    return dict(s=s, m=m, w=w, rows=rows), raw


def fill_job(args):
    s, m = args
    q, plan = D.fill_plan(s, m)
    mt = analyse_plan(plan, s, m)
    sizes = [len(t) for rnd in plan for t in rnd]
    sa = [int(A.search_result(s, m, seed, SA_ITERS).value) for seed in C.SWEEP_SEEDS]
    return dict(s=s, m=m, n=s * m, q=q, runden=mt.rounds, repeats=mt.repeats, same_dept=mt.same_dept, coverage=mt.coverage, singles=mt.singles,
                size_min=mt.size_min, size_max=mt.size_max, tables_min=mt.tables_min, tables_max=mt.tables_max,
                share_full=sum(1 for z in sizes if z == s) / len(sizes), suche_median=median(sa), suche_min=min(sa), suche_max=max(sa))


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "alle"
    path = ROOT / "data" / "trt_results.json"
    path.parent.mkdir(exist_ok=True)
    (ROOT / "tools" / "raw").mkdir(exist_ok=True)
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    data["meta"] = dict(sweep_seeds=list(C.SWEEP_SEEDS), sa_iters=SA_ITERS, greedy_seeds=C.GREEDY_SEEDS, random_trials=C.RANDOM_TRIALS, node_limit=C.NODE_LIMIT)
    with Pool(4) as pool:
        if what in ("runden", "alle"):
            data["runden"], raw = part_runden(pool)
            (ROOT / "tools" / "raw" / "runden.json").write_text(json.dumps(raw, indent=1), encoding="utf-8")
            print("runden fertig", flush=True)
        if what in ("euler", "alle"):
            data["euler"] = part_euler()
            print("euler fertig", data["euler"], flush=True)
        if what in ("abdeckung", "alle"):
            data["abdeckung"] = part_abdeckung()
            print("abdeckung fertig", flush=True)
        if what in ("budget", "alle"):
            data["budget"], raw = part_budget(pool)
            (ROOT / "tools" / "raw" / "budget.json").write_text(json.dumps(raw, indent=1), encoding="utf-8")
            print("budget fertig", data["budget"], flush=True)
        if what in ("auffuellen", "alle"):
            data["auffuellen"] = list(pool.imap(fill_job, FILL_CASES))
            print("auffuellen fertig", flush=True)
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
