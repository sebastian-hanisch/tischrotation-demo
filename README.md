# Tischrotation: Wer sitzt wann neben wem? – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-tischrotation-demo.streamlit.app/)**

Fall-Demo für die Website „Sebastian Hanisch – Operations Research und Machine Learning“ (Themenseite „Sitzplätze optimieren“). Eine **Firmenfeier** mit s Abteilungen zu je m Personen: In jeder Runde wird neu an **m Tische zu s Personen** gesetzt, an jedem Tisch eine Person je Abteilung. Gefragt ist, wie viele Runden es gibt, in denen **sich kein Paar ein zweites Mal begegnet**, und welches Verfahren sie findet: **Zufall, Greedy, Annealing** oder eine **Körper-Konstruktion** aus der Designtheorie. Dazu die Schranke, ein exakter Löser (CP-SAT) für kleine Feiern und ein Schalter für einen **zusätzlichen Tisch** („Auffüllen und Streichen“).

## Warum dieses Problem

Wer Abteilungen auf einer Feier mischen will, setzt jede Runde neu. Dass sich zwei Menschen zum zweiten Mal am Tisch treffen, während andere sich noch nie gesehen haben, ist die Wiederholung, die der Plan vermeiden soll. Die Demo fragt: **Wie viele Runden ohne Wiederholung gehen, und warum findet eine Suche weniger, als eine Konstruktion kennt?** Das Problem heißt in der Literatur Social-Golfer-Problem (Abteilungsmischung ist die Fassung mit einer Person je Abteilung am Tisch).

## Modell

- **Gegeben:** Abteilungen d = 1…s mit je m Personen; w Runden mit je m Tischen zu s Plätzen; an jedem Tisch sitzt genau eine Person je Abteilung.
- **Gesucht:** ein Plan, in dem sich kein Paar aus verschiedenen Abteilungen zweimal am Tisch begegnet. Eine **Wiederholung** ist eine zweite Begegnung desselben Paares; jede zählt eins.
- **Schranke:** Jede Person trifft je Runde genau eine Person jeder anderen Abteilung; nach m Runden kennt sie alle, die (m + 1)-te Runde enthält eine Wiederholung. Bei **s > m** gibt es nur **eine** Runde: die s Personen eines Tisches müssten sich in der nächsten Runde auf m < s Tische verteilen (Schubfachprinzip).
- **Körper-Konstruktion:** Ist m eine Primzahlpotenz und s ≤ m, sitzt Person i der Abteilung d in Runde r an Tisch t, wenn i = t + r·d in einem Körper mit m Elementen. Dann sitzt jedes Paar aus verschiedenen Abteilungen genau einmal zusammen: m Runden, die Schranke.
- **Auffüllen und Streichen** (Schalter): für m, das kein Körper ist, die Konstruktion für die nächste Körperordnung q ≥ max(m, s) bilden und in jeder Abteilung die Personen mit Nummer ≥ m streichen. Ergebnis: q Runden ohne Wiederholung, aber bis zu q Tische statt m und Tische mit bis zu q − m Personen weniger als s.
- Das vollständige Modell der exakten Entscheidung (Variablen, Nebenbedingungen, Symboltabelle) steht im 📐-Expander der App; Annahmen und Grenzen im Expander „🚧 Wo die Annahmen enden“.

## Methodik

| Verfahren | Wie es arbeitet | Grenze |
|---|---|---|
| **Zufall** | zufällige Runden bis zur ersten Wiederholung (Mittel über 200 Zufallsfolgen) | ab drei Abteilungen enthält schon die zweite Runde fast immer eine Wiederholung; bei zwei Abteilungen in etwa der Hälfte bis zwei Dritteln der Folgen (`test_zufall_bei_zwei_abteilungen_ist_haeufiger_wiederholungsfrei`) |
| **Greedy** | jede Runde ist eine zulässige Runde bezüglich aller früheren (Tiefensuche mit Zurücksetzen, Knotenlimit 30 000 je Runde); Median über 5 Zufalls-Seeds | frühe Runden verbauen spätere; in 6×7, 6×8 und 4×10 endet die Suche meist am Knotenlimit, dann ist „keine Runde gefunden“ kein Nachweis, dass keine existiert |
| **Annealing** | Runden schrittweise hinzufügen; Personen derselben Abteilung zwischen Tischen derselben Runde tauschen, Kosten = überzählige Begegnungen; **feste Temperatur 0,25, kein Abkühlplan** (ein Metropolis-Verfahren); Budget 0,3 / 1 / 3 Mio. **Zugvorschläge** je Rundenzahl (Vorschläge, bei denen die gewählte Person an keiner Wiederholung beteiligt ist, werden zu 95 % ohne Bewertung übersprungen; der Anteil an allen Vorschlägen liegt darunter) | bleibt vor der Schranke stehen |
| **Körper-Konstruktion** | siehe Modell | braucht m als Primzahlpotenz und s ≤ m |
| **Auffüllen und Streichen** | siehe Modell | mehr Tische, kleinere Tische |
| **Exakt (CP-SAT)** | entscheidet „gibt es w Runden“; Symmetriebrechung: Runde 0 und Abteilung 0 fest, in Abteilung 1 sitzt in Runde r Person r an Tisch 0; Zeitlimit 20 s, „nicht entschieden“ ist kein Beweis | nur bis 24 Personen |

**Einheit des Vergleichs:** überall **Runden ohne Wiederholung** (Zufall: Mittel, Greedy: Median, übrige: ein Lauf). Alle Zufallsfolgen kommen aus einem eigenen SplitMix64. Bei Suche und Greedy ist das Budget eine Zahl von Zugvorschlägen bzw. Knoten, nicht von Sekunden; nur der exakte Löser hat ein Zeitlimit in Sekunden.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stammen aus `data/trt_results.json` (`tools/make_results.py`; feste Zufalls-Seeds 100000 bis 100004; Annealing mit 3 Mio. Zugvorschlägen je Rundenzahl; Greedy-Median über 5 und Zufall-Mittel über 200 Unter-Seeds je Zufalls-Seed, Unter-Seeds seed·1000 + k ohne Überlappung, also 25 bzw. 1000 verschiedene). `tests/test_claims.py` rechnet davon nur 3 der 14 Größen (3×4, 3×5, 4×5), die Euler-Tabelle, die 10 Auffüllen-Größen und eine Budgetzelle neu und zählt den Rest gegen die Datei; die Spalte „Test“ nennt die Prüfung. Alle Verhaltens- und Instanzparameter sind Annahmen.

| Frage | Befund | Test |
|---|---|---|
| Erreicht die Konstruktion die Schranke? | In **8 von 8** Größen mit Körper (3×4, 3×5, 3×7, 4×5, 4×7, 4×8, 6×7, 6×8; Abteilungen × Personen je Abteilung) gibt sie m Runden, jedes Fremdpaar genau einmal | `test_konstruktion_hat_in_8_von_14_groessen_m_runden_und_in_6_keine` |
| Schlägt sie die Suche? | Der Median des Annealings liegt in **5 von 8** dieser Größen unter der Konstruktion (3×7: 6 gegen 7; 4×7: 5 gegen 7; 4×8: 5 gegen 8; 6×7: 3 gegen 7; **6×8: 3 gegen 8**); in den anderen 3 (3×4, 3×5, 4×5) erreicht er sie im Median (3×4 und 3×5 in 5 von 5 Zufalls-Seeds, 4×5 in 4 von 5). Das gilt für dieses Annealing mit fester Temperatur und 3 Mio. Zugvorschlägen | `test_annealing_liegt_in_5_von_8_groessen_mit_konstruktion_unter_der_konstruktion` |
| Und ohne Konstruktion (m = 6 oder 10)? | In **6 von 6** Größen liegt der Median des Annealings unter der Schranke m (3×6: 5 von 6; 4×6: 5; 5×6: 5; 6×6: 2; 3×10: 8; 4×10: 6). Bei m = 6 und s ≥ 3 ist die Schranke aber nicht erreichbar: 6 Runden bei 3 Abteilungen sind bewiesen unmöglich, und jeder Plan mit mehr Abteilungen enthält durch Weglassen von Abteilungen einen Plan für 3 Abteilungen; das Annealing erreicht dort im Median 5, bei 3×6 das Optimum. Für m = 10 ist offen, was erreichbar ist | `test_annealing_erreicht_in_der_messreihe_nie_die_schranke_bei_m_gleich_6_oder_10`, `test_teilplan_aus_drei_abteilungen_ist_zulaessig` |
| Wie gut ist der Greedy? | Sein Median liegt in 14 von 14 Größen nie über dem des Annealings, in **12** darunter, in 2 gleich (6×6, 6×8). In 6×7, 6×8 und 4×10 endet der Greedy in 24, 25 bzw. 17 von je 25 Läufen am Knotenlimit (nicht vollständig durchsucht), in allen anderen Größen in keinem | `test_greedy_median_liegt_nie_ueber_dem_annealing_in_12_von_14_darunter_in_2_gleich`, `test_greedy_endet_nur_in_drei_groessen_am_knotenlimit` |
| Und Zufallsrunden? | Im Mittel höchstens **1,05** Runden in allen 14 Größen (alle mit s ≥ 3; zwischen 1,00 und 1,05, die Streuung der 1000 Zufallsfolgen je Größe liegt im Bereich dieser Zahlen). Bei zwei Abteilungen enthält die zweite Runde nur in etwa der Hälfte bis zwei Dritteln der Folgen eine Wiederholung (400 Folgen je Größe; 2 Abteilungen mit 2, 3, 5, 8 und 12 Personen je Abteilung) | `test_zufallsrunden_geben_im_mittel_hoechstens_1_05_runden`, `test_zufall_bei_zwei_abteilungen_ist_haeufiger_wiederholungsfrei` |
| Was bringt die Euler-Barriere? | 3 Abteilungen zu 6: **5 Runden möglich, 6 bewiesen unmöglich** (CP-SAT mit der Symmetriebrechung der App; die Symmetriebrechung ist gegen ein Modell ohne Brechung an 6 kleineren Fällen bis 4×4 geprüft, für 3×6 deckt der Satz von Tarry die Antwort, in der Vormessung beweist auch das Modell mit nur fester Runde 0 die Unmöglichkeit, 208 s mit 4 Arbeitern, nicht im Test); kleinere Fälle 3×2: 2 Runden unmöglich, 3×3, 3×4, 3×5: so viele wie Tische | `test_euler_tabelle_stimmt_mit_dem_loeser_ueberein`, `test_euler_fall_3x6_fuenf_runden_ja_sechs_unmoeglich`, `test_symmetriebrechung_aendert_die_antwort_nicht` |
| Was leistet Auffüllen und Streichen? | In **10 von 10** Größen (3×6, 4×6, 5×6, 6×6, 3×10, 4×10, 6×10, 3×12, 4×12, 6×14; alle mit s ≥ 3 und s ≤ m) gibt es q Runden ohne Wiederholung, jedes Fremdpaar genau einmal, keine Einzelperson am Tisch. 3×6: **7 Runden** (Schranke bei 6 Tischen: 6, erreichbar höchstens 5; Annealing 5); 6×6: 7 (Annealing 2). In 10 von 10 liegt der Wert über Annealing und Schranke, auch weil das Verfahren zusätzliche Tische nimmt (q statt m; ab Runde 2 bis zu q Tische, Runde 1 hat m). Einzelpersonen am Tisch entstehen beim Auffüllen auch bei gleich großen Abteilungen: 2×6, 2×10, 2×12 und 6×2 haben je 12, 20, 24 und 12 davon (alle Runden zusammen) | `test_auffuellen_gibt_in_10_von_10_groessen_q_runden_ohne_wiederholung_und_ohne_einzelpersonen`, `test_auffuellen_liegt_in_10_von_10_groessen_ueber_dem_annealing_und_ueber_der_schranke`, `test_einzelpersonen_beim_auffuellen_auch_bei_gleich_grossen_abteilungen` |
| Wie viel vergeudet der Zufall? | 4 Abteilungen zu 5: nach 5 Runden hat die Konstruktion alle Fremdpaare zusammengebracht (100 %), zufällige Runden im Mittel 67,2 % (Formel 1 − (1 − 1/m)^R = 67,2 %; 2000 Zufallsfolgen) | `test_zufallsabdeckung_folgt_der_formel_1_minus_1_minus_1_durch_m_hoch_r` |
| Hilft mehr Rechenzeit? | Etwas, aber sie löst es nicht: 6 Abteilungen zu 8, 4 Runden: nach 0,3, 3 und 30 Mio. Zugvorschlägen bleiben mindestens **2, 2 und 1** Wiederholungen übrig (Minimum der 3 Zufalls-Seeds; Summe über die 3 Zufalls-Seeds 7, 6 und 4; in 9 von 9 Läufen bleibt mindestens eine). Gemessen an einer Größe und 3 Zufalls-Seeds | `test_rechenbudget_30_mio_zuege_lassen_mindestens_eine_wiederholung_uebrig` (die 3- und 30-Mio.-Zeilen sind Messung dieser README, nicht im Test neu gerechnet) |
| Was gilt bei mehr Abteilungen als Personen je Abteilung? | Nur **1 Runde** (4×3 durch Aufzählung aller Runden; 4×3 und 5×4 vom Löser bewiesen) | `test_bei_mehr_abteilungen_als_personen_je_abteilung_gibt_es_nur_eine_runde`, `test_maximale_rundenzahl_kleiner_faelle_durch_aufzaehlung` |

### Befunde und Korrekturen gegenüber der Vormessung

- **Die Schranke m gilt nur für s ≤ m.** Die Vormessung nannte m allgemein; bei s > m ist die Schranke 1 (Zeile oben). Die App zeigt die richtige Schranke.
- **Vormessungszahlen sind Erwartungen:** mit dem Zufallsgenerator der Demo neu gemessen. 4×6 liegt beim Annealing zwischen 4 und 5, in der Messreihe dieser README bei 5 (Median).
- **Messdesign korrigiert (unabhängiger Aussagenprüfer, 2026-11-12):** Die erste Fassung der Messreihe zog die Unter-Seeds der Zufallsfolgen und des Greedy als Zufalls-Seed + k, sodass sich benachbarte Zufalls-Seeds überlappten (204 statt 1000 verschiedene Zufallsfolgen, 9 statt 25 Greedy-Läufe). Jetzt seed·1000 + k; neu gemessen wurden Zufall (Mittel höchstens 1,05 statt 1,08) und Greedy (12 statt 11 Größen unter dem Annealing). Annealing, Auffüllen, Euler und Budget sind unverändert.
- **Tischgrößen beim Auffüllen:** bis zu q − m Personen weniger als s (nicht immer eine weniger); in der Messreihe hat keine der 10 Größen eine Einzelperson am Tisch.
- **Kein Neuheitsanspruch:** Für „Streichen aus einem Transversal-Design als Planungsregel“ habe ich keine Quelle gefunden (nur Suchtreffer, keine Volltexte); die Technik ist in der Designtheorie vermutlich bekannt. Zum Euler-Fall: Tarry (1900/1901) gilt laut Zusammenfassungen als erster Beweis, dass es keine zwei orthogonalen lateinischen Quadrate der Ordnung 6 gibt. 3 Abteilungen zu 6 mit 6 Runden ist genau dieses Paar (Zusammenfassungen gelesen, Volltexte nicht).

## Ehrliche Grenzen

- Die Suche ist ein einfaches Metropolis-Verfahren mit fester Temperatur 0,25 (kein Abkühlplan; die Temperatur wurde in der Vormessung an drei Instanzen gewählt, nicht an den hier gemessenen Größen abgestimmt); das Budget zählt Zugvorschläge, von denen diejenigen, bei denen die gewählte Person an keiner Wiederholung beteiligt ist, zu 95 % ohne Bewertung verworfen werden (der Anteil an allen Vorschlägen liegt darunter), nicht bewertete Tauschzüge. Andere Verfahren aus der Literatur (z. B. Tabu-Suche, memetische Verfahren) können mehr Runden finden. „Struktur schlägt Suche“ gilt für das hier gemessene Annealing mit den genannten Budgets, nicht für jede Suche (Schmand, Schröder, Vargas Koch: *A Greedy Algorithm for the Social Golfer and the Oberwolfach Problem*, arXiv:2007.10704, nur Zusammenfassung gelesen, behandelt eine Greedy-Garantie).
- Das Modell kennt nur **gleich große Abteilungen**. Bei sehr ungleichen Abteilungen entstehen beim Auffüllen Tische mit nur einer Person (Vormessung außerhalb dieser Demo, nicht im Test); Einzelpersonen entstehen beim Auffüllen auch bei gleich großen Abteilungen (siehe Befunde).
- **Wünsche und Sperrpaare** sowie **Sitznachbarn am runden Tisch** sind nicht modelliert; jede Wiederholung zählt gleich viel.
- Dass die Feier mehr Tische und kleinere Tische **akzeptiert**, ist eine Annahme des Schalters, keine Messung.
- Die Messreihe nutzt 5 Zufalls-Seeds; Zellen mit einer Spanne (4×5: Annealing 3 bis 5) sind nicht stabil, daher der Median.
- Suche, Greedy und Zufall laufen live nur bis 60 Personen; darüber stehen nur die Konstruktion und das Auffüllen zur Verfügung.

## Verifikation

- **Kern:** Körper GF(4) von Hand, Konstruktion 2×2 und Auffüllen 3×2 von Hand (`tests/conftest.py`: Mini-Plan), Zufallsgenerator gegen die Referenzwerte von SplitMix64, Prüfer gegen Handwerte, Randfälle (kleinste Feier, s > m, Reglergrenzen, Auffüllen ohne Wirkung).
- **Orakel (`tests/test_oracle_tischrotation.py`):** Begegnungszähler über die Inzidenzmatrix N·Nᵀ (numpy) für Konstruktion, Auffüllen, Greedy, Zufall und einen Plan mit Wiederholungen; Existenz („jedes Fremdpaar genau einmal“) für 10 Größen der Konstruktion und 8 des Auffüllens; **größte Rundenzahl kleiner Fälle durch vollständige Aufzählung** aller Runden (7 Größen) gegen den Löser, die Verfahren und die Konstruktion; CP-SAT ohne Symmetriebrechung gegen das Modell der App (6 kleine Fälle bis 4×4; 3×6 nicht, dort deckt der Satz von Tarry die Antwort); Zufallsabdeckung gegen 1 − (1 − 1/m)^R.
- **Zahlen:** `tests/test_claims.py` zählt jede Aussage der Befund-Tabelle über das ganze Raster und rechnet die schnellen Zeilen der Datei neu.
- **Verdikte:** reine Funktionen in `trt_evaluation.py`, an handgesetzten Werten und für jedes Preset geprüft (`tests/test_verdicts.py`).
- **Presets, Layout, Oberfläche:** Vollständigkeit und Werte der Presets; Schnellstart oben in der Seitenleiste, fester Kopf, aktives Preset hervorgehoben, jede Regleränderung hebt die Markierung auf; AppTest (jeder Button, jeder Regler am Minimum und Maximum, Auffüllen-Schalter, Planauswahl, Exakt-Tab beweist den Euler-Fall, Permalink); Footer; Laufzeit-Importe.
- **Testzahl:** 169 Tests (`pytest --collect-only -q tests`).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `data/trt_results.json` | vorgerechnete Messreihen (Rohdaten in `tools/raw/`) |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tools/make_results.py` | erzeugt `data/trt_results.json` mit festen Zufalls-Seeds |
| `trt_algorithm.py` | Koordinator: alle Verfahren für eine Feier, in derselben Zähleinheit |
| `trt_check.py` | Prüfer: Begegnungszähler, Wiederholungen, Abdeckung, Einzelpersonen |
| `trt_constants.py` | Regler-Grenzen, feste Annahmen, Farben, Presets |
| `trt_designs.py` | Körper-Konstruktion, Auffüllen und Streichen |
| `trt_evaluation.py` | Verdikte (reine Funktionen), Zugriff auf die vorgerechneten Messreihen |
| `trt_exact.py` | exakte Entscheidung mit CP-SAT |
| `trt_field.py` | endliche Körper GF(q) |
| `trt_layout.py` | Fester Kopf (Stylesheet) |
| `trt_presets.py` | Permalink, Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `trt_rng.py` | eigener Zufallsgenerator (SplitMix64) |
| `trt_scenario.py` | Firmenfeier: Beschriftung der Personen und Abteilungen |
| `trt_search.py` | Zufall, Greedy, Annealing |
| `trt_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Kern, Randfälle, Orakel, Zahlen, Verdikte, Presets, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Ungleich große Abteilungen**, **Wünsche und Sperrpaare**, **Sitznachbarn am runden Tisch (Oberwolfach-Problem)**, Tische ungleicher Größe: eigene Modelle; die Demo bleibt bei der Abteilungsmischung.
- **PDF-Export** und eine Sekundenmessung der Verfahren: die Aussage der Demo sind Rundenzahlen, keine Laufzeiten.
- **Weitere Suchverfahren** (Tabu-Suche, memetische Verfahren): eine Aussage über die Suche als Klasse ist damit nicht möglich.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und OR-Tools (CP-SAT).

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zum Thema: [Sitzplätze optimieren](https://sebastianhanisch.net/sitzplaetze-optimieren.html).
