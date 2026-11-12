"""Tischrotation: Wer sitzt wann neben wem? - interaktive Fall-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Eine Firmenfeier mit s Abteilungen à m Personen: In jeder Runde wird neu an m Tische zu s Personen gesetzt, an jedem Tisch eine Person je Abteilung.
Gefragt ist, wie viele Runden es ohne Wiederholung gibt (Paare, die sich nicht zum zweiten Mal begegnen) und welches Verfahren sie findet.

Lauffähig mit: streamlit run app.py
"""

import pandas  # noqa: F401  (früh importiert, Vorsichtsmaßnahme gegen einen Importfehler beim Kaltstart der Cloud-App)
import streamlit as st

import trt_constants as C
from trt_evaluation import Settings, analyse, load_results, verdict_exact, verdict_fill, verdict_rounds
from trt_layout import dunkles_design, kopf_css
from trt_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from trt_scenario import Party
from trt_visualization import build_abdeckung, build_budget, build_fill, build_meetings, build_methods, build_plan_matrix, build_runden

st.set_page_config(page_title="Tischrotation – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _exact(s, m, w):
    import trt_exact as X

    return X.exists_rounds(s, m, w, time_limit=C.EXACT_TIME_LIMIT, workers=2)


ASSUMPTIONS_MARKDOWN = """
| Annahme | Wer setzt an |
|---|---|
| An jedem Tisch sitzt genau eine Person je Abteilung (kein Paar derselben Abteilung); alle Tische haben s Plätze, es gibt m Tische | Modell dieser Demo |
| Eine Wiederholung ist eine zweite Begegnung desselben Paares an einem Tisch; wie schlimm sie ist, geht nicht ein (jede zählt eins) | Modell dieser Demo |
| Alle Abteilungen sind gleich groß | Modell dieser Demo (ungleiche Abteilungen sind nicht umgesetzt) |
| Der Zufalls-Seed legt Zufallsrunden, Greedy und Annealing fest; die Konstruktion hängt nur an (s, m) | Demo |
| Zusätzliche Tische (Schalter) heißt: q Tische statt m, wobei q die nächste Körpergröße ist; Tische mit weniger als s Personen (bis zu q − m weniger) sind für die Feier akzeptabel | Wählbare Annahme |
| Wünsche, Sperrpaare, Sitznachbarn am runden Tisch und Tischgrößen ungleich s sind nicht modelliert | Nicht umgesetzt |
"""

# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in trt_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🪑 Tischrotation: Wer sitzt wann neben wem?")
st.markdown(
    """
Auf einer **Firmenfeier** mit **s Abteilungen** zu je **m Personen** wird in jeder **Runde** neu an **m Tische zu s Personen** gesetzt, an jedem Tisch eine Person je Abteilung.
Wie viele Runden gibt es, in denen **sich kein Paar ein zweites Mal begegnet**, und welches Verfahren findet sie: Zufall, Greedy, Annealing oder eine **Körper-Konstruktion** aus der Designtheorie?
Dazu die Schranke (mehr als m Runden gehen nicht) und ein Schalter für einen **zusätzlichen Tisch** („Auffüllen und Streichen“).

Weiter unten: die **Kernfrage**, vier **Experimente** mit vorgerechneten Messreihen und der Expander **🔧 Wie wir das erreichen – vollständiger Methodenvergleich**.
"""
)

# erklaerseite:einfach:start (erzeugt von tools/set_demo_explainer.py (Website-Repo) aus tools/content/explainers/tischrotation-erklaert.json, nicht von Hand ändern)
with st.expander("💬 In einfachen Worten"):
    st.markdown(
        """
Hier feiert eine Firma mit mehreren Abteilungen. In jeder Runde wird neu an Tische gesetzt, an jedem Tisch sitzt eine Person aus jeder Abteilung. Die Frage ist, wie viele Runden es gibt, in denen sich kein Paar ein zweites Mal am Tisch begegnet, und welches Verfahren solche Runden findet.

Die App vergleicht zufällige Runden, ein Verfahren, das Runde für Runde eine zulässige wählt, eine Suche mit Tauschen und eine Konstruktion nach einer Rechenregel. Sie zeigt die Schranke für die Rundenzahl, kann für kleine Feiern klären, ob eine Rundenzahl geht, und rechnet, was ein zusätzlicher Tisch bringt. Die Feier ist ausgedacht, es sind keine echten Personen.

[Ausführlich und verständlich erklärt, mit Fachteil](https://sebastianhanisch.net/tischrotation-erklaert.html)
        """
    )
# erklaerseite:einfach:end
st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Feier**")
    s = st.slider("Abteilungen s (= Personen je Tisch)", *bounds("s_slider"), key="s_slider", help="Wie viele Abteilungen es gibt; an jedem Tisch sitzt eine Person je Abteilung.")
    m = st.slider("Personen je Abteilung m (= Tische je Runde)", *bounds("m_slider"), key="m_slider", help="Wie viele Personen jede Abteilung hat; das ist zugleich die Zahl der Tische.")
    st.markdown("**Verfahren**")
    fill = st.toggle("Zusätzliche Tische erlauben (Auffüllen und Streichen)", key="fill_toggle",
                     help="Mehr Tische und Tische mit weniger Personen erlauben mehr Runden. Ausgeschaltet gelten genau m Tische zu s Personen.")
    budget = st.select_slider("Rechenbudget des Annealings", options=list(range(len(C.BUDGETS))), key="budget_slider",
                              format_func=lambda i: C.BUDGET_LABELS[i], help="Zugvorschläge je Rundenzahl (die meisten werden ohne Bewertung verworfen); mehr Budget dauert bei größeren Feiern spürbar länger.")
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neuer Zufalls-Seed", width="stretch", on_click=randomize_seed)

sync_query_params({"s_slider": int(s), "m_slider": int(m), "fill_toggle": bool(fill), "budget_slider": int(budget), "seed_input": int(seed)})

settings = Settings(int(s), int(m), int(seed), bool(fill), int(budget))
party = Party(settings.s, settings.m)
if party.n <= C.N_LIVE_MAX:
    with st.spinner("Suche und Greedy rechnen …"):
        a = _analysis(settings)
else:
    a = _analysis(settings)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
if a.best_key() is None:
    st.info(f"Für {party.s} Abteilungen zu {party.m} Personen gibt es hier keinen Plan: ohne Körper-Konstruktion laufen Suche, Greedy und Zufall nur bis {C.N_LIVE_MAX} Personen. "
            "Schalter „Zusätzliche Tische erlauben“ einschalten oder die Feier verkleinern.")
else:
    options = ["Beste gefundene Lösung"] + [a.results[k].label for k in a.results if a.results[k].available and a.results[k].plan]
    view = st.selectbox("Plan anzeigen", options, key="view_select", help="Welcher Plan unten gezeigt wird; Zufall und Greedy zeigen den Plan des ersten Zufalls-Seeds.")
    shown_key = a.best_key() if view == options[0] else next(k for k in a.results if a.results[k].label == view)
    shown = a.results[shown_key]
    mt = shown.metrics

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Runden", f"{mt.rounds}", help=f"Verfahren: {shown.label}")
    m2.metric("Schranke (m Tische zu s)", f"{a.bound}")
    m3.metric("Wiederholungen im Plan", f"{mt.repeats}")
    m4.metric("Begegnete Fremdpaare", f"{mt.coverage * 100:.1f} %".replace(".", ","))
    st.caption(f"Gezeigt: **{shown.label}**" + (f" – {shown.note}" if shown.note else "") + f" Tische je Runde: {mt.tables_min}" + (f" bis {mt.tables_max}" if mt.tables_max != mt.tables_min else "")
               + f"; Personen je Tisch: {mt.size_min}" + (f" bis {mt.size_max}" if mt.size_max != mt.size_min else "") + f"; Einzelpersonen am Tisch: {mt.singles}.")

    r_idx = st.slider("Runde ansehen", 1, mt.rounds, 1, key="round_view", help="Zeigt die Tische der gewählten Runde in Worten.") if mt.rounds > 1 else 1
    tables = shown.plan[r_idx - 1]
    st.markdown(f"**Runde {r_idx}:** " + " · ".join(f"Tisch {t + 1}: " + ", ".join(party.label(p) for p in table) for t, table in enumerate(tables)))
    tab_plan, tab_meet = st.tabs(["Plan: Tisch je Person und Runde", "Begegnungsmatrix"])
    with tab_plan:
        st.plotly_chart(build_plan_matrix(shown.plan, party), width="stretch", key="plan_chart")
        st.caption("Zeilen: Personen (Buchstabe = Abteilung), Spalten: Runden. Gleiche Zahl und Farbe in einer Spalte = gleicher Tisch.")
    with tab_meet:
        st.plotly_chart(build_meetings(shown.plan, party), width="stretch", key="meet_chart")
        st.caption("Grau: gleiche Abteilung, hell: noch nie am selben Tisch, grün: genau einmal, rot: mehrfach.")

    st.plotly_chart(build_methods(a.results, a.bound), width="stretch", key="methods_chart")
    st.caption("Wiederholungsfreie Runden je Verfahren (Zufall: Mittel über Zufallsfolgen, Greedy: Median über Zufalls-Seeds, Annealing: ein Lauf, Konstruktion: exakt).")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wie viele Runden ohne Wiederholung, und welches Verfahren schafft sie?")
kind, text = verdict_rounds(a)
getattr(st, kind)(text)
if settings.fill:
    kind, text = verdict_fill(a)
    getattr(st, kind)(text)

st.markdown("---")

# --- Experimente (vorgerechnet) ------------------------------------------------------------------------------------------------------------

R = load_results()
st.markdown("## 🔬 Experimente (vorgerechnet, feste Zufalls-Seeds)")
st.caption(f"Alle Zahlen dieses Abschnitts stammen aus `data/trt_results.json` (Zufalls-Seeds {R['meta']['sweep_seeds'][0]} bis {R['meta']['sweep_seeds'][-1]}, "
           f"Annealing mit {R['meta']['sa_iters'] // 1_000_000} Mio. Zugvorschlägen je Rundenzahl, Unter-Seeds seed·1000 + k) und werden von `tests/test_claims.py` zum Teil neu gerechnet, im Übrigen gegen die Datei gezählt.")

st.subheader("1 · Konstruktion gegen einfaches Annealing")
st.plotly_chart(build_runden(R["runden"]), width="stretch", key="runden_chart")
rows = R["runden"]
cons_rows = [r for r in rows if r["konstruktion"]]
st.info(f"In {sum(1 for r in cons_rows if r['suche_median'] < r['konstruktion'])} von {len(cons_rows)} Größen mit Konstruktion liegt der Median des Annealings unter dem Wert der Konstruktion; "
        f"im größten Fall (6×8, 48 Personen) sind es {next(r for r in rows if r['s'] == 6 and r['m'] == 8)['suche_median']:.0f} Runden gegen "
        f"{next(r for r in rows if r['s'] == 6 and r['m'] == 8)['konstruktion']}.")

st.subheader("2 · Die Euler-Barriere und der zusätzliche Tisch")
eu = R["euler"]
st.dataframe(
    [{"Abteilungen × Personen": f"{e['s']}×{e['m']}", "Runden": e["w"], "CP-SAT": {"ja": "möglich (Plan gefunden)", "unmöglich": "bewiesen unmöglich", "unentschieden": "nicht entschieden"}[e["status"]]} for e in eu],
    hide_index=True, width="stretch")
st.plotly_chart(build_fill(R["auffuellen"]), width="stretch", key="fill_chart")
fi = {(f["s"], f["m"]): f for f in R["auffuellen"]}
st.info(f"Bei 3 Abteilungen zu 6 Personen sind 5 Runden möglich und 6 bewiesen unmöglich; mit einem zusätzlichen Tisch gibt es {fi[(3, 6)]['runden']} Runden ohne Wiederholung, "
        f"in {sum(1 for f in R['auffuellen'] if f['repeats'] == 0 and f['same_dept'] == 0)} von {len(R['auffuellen'])} gerechneten Größen ohne jede Wiederholung. "
        f"Einzelpersonen am Tisch: {sum(f['singles'] for f in R['auffuellen'])} über alle {len(R['auffuellen'])} Größen.")

st.subheader("3 · Zufall vergeudet Begegnungen")
ab = R["abdeckung"]
st.plotly_chart(build_abdeckung(ab), width="stretch", key="abdeckung_chart")
last = ab["rows"][-1]
st.info(f"Bei {ab['s']} Abteilungen zu {ab['m']} Personen sind nach {last['R']} Runden mit der Konstruktion alle Fremdpaare begegnet ({last['konstruktion'] * 100:.0f} %), "
        f"mit zufälligen Runden im Mittel {last['zufall'] * 100:.1f} % (Formel 1 − (1 − 1/m)^R: {last['formel'] * 100:.1f} %).".replace(".", ","))

st.subheader("4 · Mehr Rechenzeit: weniger Wiederholungen, aber keine Lösung")
bu = R["budget"]
st.plotly_chart(build_budget(bu), width="stretch", key="budget_chart")
st.info(f"Bei {bu['s']} Abteilungen zu {bu['m']} Personen und {bu['w']} Runden bleiben nach 0,3, 3 und 30 Mio. Zugvorschlägen mindestens "
        f"{bu['rows'][0]['rest_min']}, {bu['rows'][1]['rest_min']} und {bu['rows'][2]['rest_min']} Wiederholungen übrig (Minimum der {len(bu['rows'][0]['rest'])} Zufalls-Seeds; "
        f"Summe über die Zufalls-Seeds {sum(bu['rows'][0]['rest'])}, {sum(bu['rows'][1]['rest'])} und {sum(bu['rows'][2]['rest'])}).")

st.markdown("---")

# --- Methodenvergleich ---------------------------------------------------------------------------------------------------------------------

with st.expander("🔧 Wie wir das erreichen – vollständiger Methodenvergleich"):
    tab_verf, tab_exact = st.tabs(["Verfahren", "🧮 Exakt (CP-SAT)"])
    with tab_verf:
        st.markdown(
            """
| Verfahren | Wie es arbeitet | Stärke | Grenze |
|---|---|---|---|
| **Zufall** | Zufällige Runden, bis zum ersten Mal ein Paar zum zweiten Mal am Tisch sitzt | Kein Rechenaufwand | Ab drei Abteilungen enthält schon die zweite Runde fast immer eine Wiederholung (bei zwei Abteilungen in etwa der Hälfte bis zwei Dritteln der Folgen) |
| **Greedy** | Jede Runde ist eine zulässige Runde bezüglich aller früheren (Tiefensuche mit Zurücksetzen, Knotenlimit) | Findet zu jedem Stand eine zulässige Runde, wenn die Tiefensuche sie innerhalb des Knotenlimits findet | Frühe Runden verbauen spätere; in den Größen 6×7, 6×8 und 4×10 endet die Suche meist am Knotenlimit statt vollständig |
| **Annealing** | Runden schrittweise hinzufügen; Personen derselben Abteilung zwischen Tischen tauschen, bis keine Wiederholung bleibt | Findet Pläne ohne Struktur | Feste Temperatur 0,25, kein Abkühlplan; bleibt ab etwa 20 bis 25 Personen meist vor der Schranke stehen; mehr Zugvorschläge senken die Zahl der Wiederholungen nur langsam |
| **Körper-Konstruktion** | Person i der Abteilung d sitzt in Runde r an Tisch t, wenn i = t + r·d in einem Körper mit m Elementen | Erreicht die Schranke m, jedes Fremdpaar genau einmal | Braucht m als Primzahlpotenz (2, 3, 4, 5, 7, 8, 9, 11, 13) und s ≤ m |
| **Auffüllen und Streichen** | Konstruktion für die nächste Körpergröße q ≥ m, dann in jeder Abteilung die Personen mit Nummer ≥ m streichen | q > m Runden ohne Wiederholung, auch wenn m kein Körper ist | Mehr Tische (q statt m), Tische mit bis zu q − m Personen weniger; Einzelpersonen am Tisch möglich (bei s = 2, s > m und sehr ungleichen Abteilungen) |
"""
        )
        st.markdown("**Annahmen:**")
        st.markdown(ASSUMPTIONS_MARKDOWN)
    with tab_exact:
        # Der Tab ist selbstständig: eigener Button, Spinner und Ergebnis, gegen das aktuelle Szenario geprüft (DEMO-PLAYBOOK §2).
        if party.n > C.EXACT_N_MAX:
            st.info(f"Der exakte Löser läuft hier nur bis {C.EXACT_N_MAX} Personen (aktuell {party.n}).")
        else:
            w_ex = st.number_input("Runden w", 1, settings.m, min(settings.m, 6), key="exact_w", help="Gibt es w Runden ohne Wiederholung bei m Tischen zu s Personen?")
            key = (settings.s, settings.m, int(w_ex))
            if st.button("Exakt entscheiden", key="exact_start"):
                st.session_state["exact_done"] = key
            if st.session_state.get("exact_done") == key:
                with st.spinner(f"CP-SAT prüft {int(w_ex)} Runden (Zeitlimit {C.EXACT_TIME_LIMIT:.0f} s) …"):
                    status, _plan = _exact(*key)
                kind, text = verdict_exact(status, settings.s, settings.m, int(w_ex))
                getattr(st, kind)(text)

with st.expander("📐 Mathematische Formulierung"):
    # erklaerseite:lesehilfe:start (erzeugt von tools/set_demo_explainer.py (Website-Repo) aus tools/content/explainers/tischrotation-erklaert.json, nicht von Hand ändern)
    st.markdown(
        r"""
**Lesehilfe.** Gegeben sind $s$ Abteilungen mit je $m$ Personen und $w$ Runden mit je $m$ Tischen zu $s$ Plätzen; an jedem Tisch sitzt genau eine Person je Abteilung. Gesucht ist ein Plan, in dem sich kein Paar aus verschiedenen Abteilungen zweimal am Tisch begegnet. Die Formeln unten sind das vollständige Modell der exakten Entscheidung; die Konstruktion rechnet in einem endlichen Körper mit $m$ Elementen.

| Symbol | Bedeutung |
|---|---|
| $s$ | Zahl der Abteilungen, zugleich Personen je Tisch |
| $m$ | Personen je Abteilung, zugleich Tische je Runde |
| $w$ | Zahl der Runden |
| $r$ | Runde, $r = 1,\dots,w$ |
| $t$ | Tisch, $t = 1,\dots,m$ |
| $d, e$ | Abteilungen, $d, e = 1,\dots,s$ |
| $i, j$ | Personen innerhalb einer Abteilung, $i, j = 1,\dots,m$ |
| $x_{r,d,i,t}$ | 1, wenn Person $i$ der Abteilung $d$ in Runde $r$ an Tisch $t$ sitzt, sonst 0 |
| $y_{r}^{(d,i),(e,j)}$ | 1, wenn die beiden Personen in Runde $r$ an einem Tisch sitzen |
| $q$ | Größe des Körpers bei Auffüllen und Streichen: die kleinste Zahl $q \ge \max(m, s)$, für die es einen Körper mit $q$ Elementen gibt |

[Schritt für Schritt erklärt, mit Herleitung und Literatur](https://sebastianhanisch.net/tischrotation-erklaert.html#fachleute)
        """
    )
    # erklaerseite:lesehilfe:end
    st.markdown(
        r"""
**Gegeben:** Abteilungen $d = 1,\dots,s$ mit je $m$ Personen, Personen $(d, i)$ mit $i = 1,\dots,m$; $w$ Runden $r = 1,\dots,w$ mit je $m$ Tischen $t = 1,\dots,m$.
**Gesucht:** Variablen $x_{r,d,i,t} \in \{0, 1\}$ ($=1$, wenn $(d, i)$ in Runde $r$ an Tisch $t$ sitzt) mit

$$\sum_{t} x_{r,d,i,t} = 1 \quad \forall r, d, i, \qquad \sum_{i} x_{r,d,i,t} = 1 \quad \forall r, d, t,$$

$$\sum_{r} y_{r}^{(d,i),(e,j)} \le 1 \quad \forall\, d \ne e,\ i,\ j, \qquad y_{r}^{(d,i),(e,j)} \ge x_{r,d,i,t} + x_{r,e,j,t} - 1 \quad \forall r, t.$$

| Symbol | Bedeutung |
|---|---|
| $s$ | Zahl der Abteilungen, zugleich Personen je Tisch |
| $m$ | Personen je Abteilung, zugleich Tische je Runde |
| $w$ | Zahl der Runden |
| $x_{r,d,i,t}$ | Person $(d, i)$ sitzt in Runde $r$ an Tisch $t$ |
| $y_{r}^{(d,i),(e,j)}$ | die beiden Personen sitzen in Runde $r$ an einem Tisch |

Die erste Gleichung setzt jede Person genau einmal, die zweite besetzt an jedem Tisch genau eine Person je Abteilung; die Ungleichungen verbieten, dass sich ein Paar aus verschiedenen Abteilungen zweimal begegnet. Alle $x$ und $y$ sind 0/1-Variablen (für $y$ genügt $y \ge 0$); das Modell hat keine Zielfunktion, es entscheidet, ob $w$ Runden gehen, und die größte Rundenzahl ergibt sich durch Lösen für $w = 1, 2, \dots$. Es kennt nur $m$ Tische zu $s$ Plätzen; Auffüllen und Streichen liegt außerhalb dieses Modells.
**Schranke:** Jede Person trifft je Runde genau eine Person jeder anderen Abteilung; nach $m$ Runden kennt sie alle, also gilt $w \le m$.
**Körper-Konstruktion:** Für $m = q$ Primzahlpotenz und $s \le q$ sitzt $(d, i)$ in Runde $r$ an Tisch $t$, wenn $i = t + r \cdot d$ in $\mathrm{GF}(q)$; dann hat jedes Fremdpaar genau eine Runde gemeinsam ($w = m$).
**Auffüllen und Streichen:** für $q \ge m$ die Konstruktion bilden und die Personen mit $i > m$ streichen; das gibt $q$ Runden ohne Wiederholung, aber bis zu $q$ Tische mit $s$ oder weniger Personen (bis zu $q - m$ weniger).
Der Formelblock ist das vollständige Modell der exakten Entscheidung; der Löser fügt zusätzlich die Symmetriebrechung der README hinzu. Die Suchverfahren und die Konstruktion lösen dieselbe Aufgabe ohne Löser.
"""
    )

with st.expander("🚧 Wo die Annahmen enden"):
    st.markdown(
        """
- Das Modell kennt nur **gleich große Abteilungen**. Bei sehr ungleichen Abteilungen liefert Auffüllen und Streichen zwar ebenfalls keine Wiederholung, lässt aber Tische mit nur einer Person übrig (nicht gemessen in der App; ungleiche Abteilungen sind nicht umgesetzt).
- **Wünsche und Sperrpaare** (wer unbedingt oder nie neben wem sitzen soll) sind nicht modelliert; ebenso **Sitznachbarn am runden Tisch** und Tische mit ungleicher Größe.
- Dass die Feier mehr Tische und Tische mit weniger Personen **akzeptiert**, ist eine Annahme des Schalters, keine Messung. **Einzelpersonen am Tisch** entstehen beim Auffüllen auch bei gleich großen Abteilungen, etwa bei s = 2 (z. B. 2×6) oder s > m (z. B. 6×2); die App zeigt sie als Kennzahl.
- Die Suche ist ein einfaches Annealing; andere Verfahren aus der Literatur (z. B. Tabu-Suche) können mehr Runden finden. Die Aussage „die Konstruktion liegt über dem Annealing“ gilt für das hier gemessene Annealing (feste Temperatur 0,25) mit den genannten Budgets.
- Bei Suche und Greedy ist das Budget eine Zahl von **Zugvorschlägen und Knoten, nicht von Sekunden**; nur der exakte Löser hat ein Zeitlimit in Sekunden. Wie lange ein Lauf dauert, hängt vom Rechner ab.
"""
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zum Thema: [Sitzplätze optimieren](https://sebastianhanisch.net/sitzplaetze-optimieren.html)."
)
