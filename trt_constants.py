"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

S_MIN, S_MAX, DEFAULT_S = 2, 8, 6          # Abteilungen = Personen je Tisch
M_MIN, M_MAX, DEFAULT_M = 2, 12, 8         # Personen je Abteilung = Tische je Runde
SEED_MAX, DEFAULT_SEED = 999999, 35
BUDGETS = (300_000, 1_000_000, 3_000_000)  # Annealing-Zugvorschläge je Rundenzahl (die meisten werden ohne Bewertung verworfen; Tabelle in der README: 3 Mio.)
BUDGET_LABELS = ("0,3 Mio. Vorschläge", "1 Mio. Vorschläge", "3 Mio. Vorschläge")
DEFAULT_BUDGET = 1
N_LIVE_MAX = 60                            # größere Feiern: Suche, Greedy und Zufall nur in den vorgerechneten Experimenten
NODE_LIMIT = 30_000                        # Knotenlimit des Greedy je Runde
GREEDY_SEEDS = 5                           # Greedy: Median über so viele Zufalls-Seeds ab dem eingestellten
RANDOM_TRIALS = 200                        # Zufall: Mittel über so viele Zufallsfolgen
SUBSEED_STRIDE = 1000                      # Unter-Seeds eines Zufalls-Seeds: seed·1000 + k (k < 1000), damit benachbarte Zufalls-Seeds sich nicht überlappen
SWEEP_SEEDS = tuple(range(100000, 100005))  # feste Zufalls-Seeds aller vorgerechneten Messreihen: nie ein einzelner Seed als Befund
EXACT_N_MAX = 24                           # Exakt-Tab: höchstens so viele Personen (CP-SAT-Zeitlimit unten)
EXACT_TIME_LIMIT = 20.0

COLOR_BEST = "#2F6B65"
COLOR_OTHER = "rgba(150,150,150,0.55)"
COLOR_LINE = "#4c78a8"
COLOR_WARN = "#c0504d"

PRESETS = {
    "Firmenfeier 48": {"s": 6, "m": 8, "fill": False, "budget": 1, "seed": DEFAULT_SEED},
    "Euler-Fall 18": {"s": 3, "m": 6, "fill": False, "budget": 1, "seed": DEFAULT_SEED},
    "Auffüllen 36": {"s": 6, "m": 6, "fill": True, "budget": 1, "seed": DEFAULT_SEED},
    "Mittlere Feier 40": {"s": 4, "m": 10, "fill": True, "budget": 1, "seed": DEFAULT_SEED},
    "Kleine Feier 15": {"s": 3, "m": 5, "fill": False, "budget": 1, "seed": DEFAULT_SEED},
}
PRESET_HELP = {
    "Firmenfeier 48": "6 Abteilungen mit je 8 Personen, 8 Tische zu 6: eine Körper-Konstruktion kennt jedes Paar genau einmal, die Suche bleibt weit darunter.",
    "Euler-Fall 18": "3 Abteilungen mit je 6 Personen, 6 Tische zu 3: die Tischzahl 6 hat keine Körper-Konstruktion; im Exakt-Tab lässt sich prüfen, ob 6 Runden gehen.",
    "Auffüllen 36": "6 Abteilungen mit je 6 Personen, mit Auffüllen und Streichen: bis zu 7 statt 6 Tische, Tische mit 5 oder 6 Personen, dafür 7 Runden.",
    "Mittlere Feier 40": "4 Abteilungen mit je 10 Personen, mit Auffüllen und Streichen: 11 Runden bei 10 oder 11 Tischen.",
    "Kleine Feier 15": "3 Abteilungen mit je 5 Personen, 5 Tische zu 3: alle Verfahren sind schnell, die Konstruktion erreicht 5 Runden.",
}
