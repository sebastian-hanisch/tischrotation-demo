"""Exakte Entscheidung mit CP-SAT (OR-Tools): Gibt es w Runden ohne Wiederholung, bei m Tischen à s Personen und einer Person je Abteilung am Tisch?

Variable x[r, d, i, t] = Person i der Abteilung d sitzt in Runde r an Tisch t. Symmetriebrechung (zulässig, siehe README): Runde 0 hat Person i an Tisch i, Abteilung 0 hat in jeder Runde
Person i an Tisch i, und in Abteilung 1 sitzt in Runde r Person r an Tisch 0 (die Runden 1.. sind vertauschbar). Ergebnis „unentschieden“ ist KEIN Beweis der Unmöglichkeit."""

from itertools import combinations

from trt_check import analyse_plan


def exists_rounds(s: int, m: int, w: int, time_limit: float = 20.0, workers: int = 2):
    """Ergebnis (Status, Plan oder None): Status „ja“ (Plan gefunden und geprüft), „unmöglich“ (bewiesen) oder „unentschieden“ (Zeitlimit)."""
    from ortools.sat.python import cp_model

    if w > m:
        return "unmöglich", None  # mehr als m Runden: nach m Runden kennt jede Person alle Fremden (Taubenschlag), also eine Wiederholung
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
        if d == e:
            continue
        met = []
        for r in range(w):
            v = model.NewBoolVar("")
            for t in range(m):
                model.AddBoolOr([x[r, d, i, t].Not(), x[r, e, j, t].Not(), v])
            met.append(v)
        model.Add(sum(met) <= 1)
    for r in range(w):
        for d in range(s):
            for i in range(m):
                if r == 0 or d == 0:
                    model.Add(x[r, d, i, i] == 1)
    if s >= 2:
        for r in range(1, w):
            model.Add(x[r, 1, r, 0] == 1)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = workers
    solver.parameters.random_seed = 1
    status = solver.Solve(model)
    name = solver.StatusName(status)
    if name in ("OPTIMAL", "FEASIBLE"):
        plan = [[[d * m + i for d in range(s) for i in range(m) if solver.Value(x[r, d, i, t])] for t in range(m)] for r in range(w)]
        metrics = analyse_plan(plan, s, m)
        if metrics.repeats or metrics.same_dept or not metrics.partition_ok:
            raise RuntimeError("Das Modell lieferte einen ungültigen Plan")
        return "ja", plan
    if name == "INFEASIBLE":
        return "unmöglich", None
    return "unentschieden", None
