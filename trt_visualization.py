"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben.
Beschriftungen der Achsen sind Text (Kategorien), damit Plotly keine lineare Achse über Zahlenfolgen legt."""

import plotly.graph_objects as go

import trt_constants as C
from trt_scenario import Party


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360, legend=True):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="rgba(0,0,0,0)", showlegend=legend,
                      legend=dict(orientation="h", y=-0.2))
    return lock_axes(fig)


def build_plan_matrix(plan, party: Party):
    """Tisch je Person (Zeilen, nach Abteilung geordnet) und Runde (Spalten): gleiche Farbe und Zahl = gleicher Tisch."""
    n = party.n
    table_of = [[0] * len(plan) for _ in range(n)]
    for r, rnd in enumerate(plan):
        for t, table in enumerate(rnd):
            for p in table:
                table_of[p][r] = t + 1
    labels = [party.label(p) for p in range(n)]
    rounds = [f"Runde {r + 1}" for r in range(len(plan))]
    fig = go.Figure(go.Heatmap(z=table_of, x=rounds, y=labels, text=table_of, texttemplate="%{text}", colorscale="Turbo", showscale=False,
                               hovertemplate="%{y}, %{x}: Tisch %{z}<extra></extra>", xgap=1, ygap=1))
    for d in range(1, party.s):
        fig.add_hline(y=d * party.m - 0.5, line=dict(color="rgba(0,0,0,0.6)", width=2))
    fig.update_yaxes(type="category", autorange="reversed")
    fig.update_xaxes(type="category", side="top")
    return _base(fig, height=max(320, 16 * n + 60), legend=False)


def build_meetings(plan, party: Party):
    """Begegnungsmatrix: gleiche Abteilung (grau), nie begegnet (hell), genau einmal (grün), mehrfach (rot)."""
    from trt_check import pair_counts

    n = party.n
    cnt = pair_counts(plan, n)
    z = [[0 if party.dept(a) == party.dept(b) else (1 if cnt[a][b] == 0 else (2 if cnt[a][b] == 1 else 3)) for b in range(n)] for a in range(n)]
    labels = [party.label(p) for p in range(n)]
    scale = [[0.0, "#bdbdbd"], [0.25, "#bdbdbd"], [0.25, "#f2efe6"], [0.5, "#f2efe6"], [0.5, C.COLOR_BEST], [0.75, C.COLOR_BEST], [0.75, C.COLOR_WARN], [1.0, C.COLOR_WARN]]
    fig = go.Figure(go.Heatmap(z=z, x=labels, y=labels, zmin=0, zmax=3, colorscale=scale, showscale=False,
                               customdata=cnt, hovertemplate="%{y} und %{x}: %{customdata}-mal am Tisch<extra></extra>"))
    fig.update_xaxes(type="category", showticklabels=party.n <= 40)
    fig.update_yaxes(type="category", autorange="reversed", showticklabels=party.n <= 40)
    return _base(fig, height=420, legend=False)


def build_methods(results: dict, bound: int):
    """Wiederholungsfreie Runden je Verfahren (live), mit der Schranke m als Linie."""
    keys = [k for k, r in results.items() if r.available]
    labels = [results[k].label for k in keys]
    values = [results[k].value for k in keys]
    colors = [C.COLOR_BEST if k in ("konstruktion", "auffuellen") else C.COLOR_LINE for k in keys]
    fig = go.Figure(go.Bar(x=labels, y=values, marker_color=colors, text=[f"{v:.1f}".rstrip("0").rstrip(".").replace(".", ",") for v in values],
                           textposition="outside", hovertemplate="%{x}: %{y:.1f} Runden<extra></extra>"))
    fig.add_hline(y=bound, line=dict(color="#555", dash="dash"), annotation_text=f"Schranke bei {bound} Tischen: {bound}", annotation_position="top left")
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="Runden ohne Wiederholung", rangemode="tozero")
    return _base(fig, legend=False)


def build_runden(rows):
    """Experiment 1: Runden je Verfahren und Größe (Median der festen Zufalls-Seeds, Zufall: Mittel)."""
    labels = [f"{r['s']}×{r['m']}" for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Zufall (Mittel)", x=labels, y=[r["zufall_mittel"] for r in rows], marker_color=C.COLOR_OTHER))
    fig.add_trace(go.Bar(name="Greedy (Median)", x=labels, y=[r["greedy_median"] for r in rows], marker_color="#9ecae1"))
    fig.add_trace(go.Bar(name="Annealing (Median)", x=labels, y=[r["suche_median"] for r in rows], marker_color=C.COLOR_LINE))
    fig.add_trace(go.Bar(name="Körper-Konstruktion", x=labels, y=[r["konstruktion"] or 0 for r in rows], marker_color=C.COLOR_BEST,
                         customdata=["" if r["konstruktion"] else "keine" for r in rows], hovertemplate="%{x}: %{y} %{customdata}<extra></extra>"))
    fig.add_trace(go.Scatter(name="Schranke m", x=labels, y=[r["schranke"] for r in rows], mode="markers", marker=dict(symbol="line-ew", size=18, color="#222",
                                                                                                               line=dict(width=2, color="#222"))))
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category", title_text="Abteilungen × Personen je Abteilung")
    fig.update_yaxes(title_text="Runden ohne Wiederholung")
    return _base(fig, height=400)


def build_fill(rows):
    """Experiment 2: Auffüllen und Streichen gegen Annealing und die Schranke m."""
    labels = [f"{r['s']}×{r['m']}" for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Annealing (Median)", x=labels, y=[r["suche_median"] for r in rows], marker_color=C.COLOR_LINE))
    fig.add_trace(go.Bar(name="Auffüllen und Streichen (mit zusätzlichem Tisch)", x=labels, y=[r["runden"] for r in rows], marker_color=C.COLOR_BEST))
    fig.add_trace(go.Scatter(name="Schranke m (gleich große Tische)", x=labels, y=[r["m"] for r in rows], mode="markers",
                             marker=dict(symbol="line-ew", size=18, color="#222", line=dict(width=2, color="#222"))))
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category", title_text="Abteilungen × Personen je Abteilung")
    fig.update_yaxes(title_text="Runden ohne Wiederholung")
    return _base(fig, height=400)


def build_abdeckung(data):
    """Experiment 3: Anteil der Paare aus verschiedenen Abteilungen, die sich nach R Runden begegnet sind."""
    rows = data["rows"]
    xs = [f"{r['R']}" for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(name="Konstruktion", x=xs, y=[r["konstruktion"] * 100 for r in rows], mode="lines+markers", line=dict(color=C.COLOR_BEST, width=3)))
    fig.add_trace(go.Scatter(name=f"Zufallsrunden (Mittel über {data['folgen']} Folgen)", x=xs, y=[r["zufall"] * 100 for r in rows], mode="lines+markers",
                             line=dict(color=C.COLOR_LINE, width=3)))
    fig.update_xaxes(type="category", title_text="Runden")
    fig.update_yaxes(title_text="Begegnete Paare (%)", range=[0, 105])
    return _base(fig)


def build_budget(data):
    """Experiment 4: Restwiederholungen des Annealings bei wachsendem Budget (Minimum über die festen Zufalls-Seeds)."""
    rows = data["rows"]
    xs = [f"{r['budget'] / 1e6:g} Mio. Vorschläge".replace(".", ",") for r in rows]
    fig = go.Figure(go.Bar(x=xs, y=[r["rest_min"] for r in rows], marker_color=C.COLOR_LINE, text=[r["rest_min"] for r in rows], textposition="outside"))
    fig.update_xaxes(type="category", title_text="Zugvorschläge für die letzte Runde")
    fig.update_yaxes(title_text="Wiederholungen übrig (Minimum der Zufalls-Seeds)", rangemode="tozero")
    return _base(fig, legend=False)
