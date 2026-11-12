"""End-to-end Smoke-Test via Streamlits offiziellem AppTest-Framework: laedt app.py mit den
Standardeinstellungen, klickt jeden Preset-Button und faehrt jeden Slider an seine Grenzen und prueft, dass
kein Python-Fehler auftritt - insbesondere `streamlit.errors.StreamlitDuplicateElementId` (mehrere
st.plotly_chart-Aufrufe ohne eindeutiges key= koennen zufaellig identischen Inhalt rendern und kollidieren)
und `StreamlitAPIException` bei Slidern mit berechneten Grenzen (min == max)."""

import os

from streamlit.testing.v1 import AppTest

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))  # unter Last (parallele Läufe) reichen 180 s nicht immer; Umgebungsvariable zum Anpassen
AUTOPLAY_MARKER = "\u25b6"  # Auto-Play-Buttons (Animation mit sleep) im Smoke-Test auslassen


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def test_app_loads_without_exception():
    _fresh_app()


def test_every_button_click_does_not_raise():
    labels = [b.label for b in _fresh_app().button]
    assert labels, "keine Buttons gefunden"
    for index, label in enumerate(labels):
        if AUTOPLAY_MARKER in label:
            continue
        at = _fresh_app()
        at.button[index].click().run(timeout=TIMEOUT)
        assert not at.exception, (label, [str(e) for e in at.exception])


def test_every_slider_at_its_min_and_max_does_not_raise():
    labels = [s.label for s in _fresh_app().slider]
    assert labels, "keine Slider gefunden"
    for index, label in enumerate(labels):
        for edge in ("min", "max"):
            at = _fresh_app()
            slider = at.slider[index]
            value = slider.min if edge == "min" else slider.max
            if isinstance(slider.value, int):
                value = int(value)
            slider.set_value(value).run(timeout=TIMEOUT)
            assert not at.exception, (label, edge, [str(e) for e in at.exception])


# --- Eigene Prüfungen der Demo ---------------------------------------------------------------------------------------------------------------


def _texts(at):
    return " ".join(x.value for x in list(at.success) + list(at.info) + list(at.warning) + list(at.error))


def test_standard_zeigt_die_konstruktion_mit_8_runden():
    at = _fresh_app()
    assert [m.value for m in at.metric][:4] == ["8", "8", "0", "100,0 %"]
    assert "**8 Runden**" in _texts(at)


def test_auffuellen_schalter_gibt_7_runden_bei_3_mal_6():
    at = _fresh_app()
    at.sidebar.slider(key="s_slider").set_value(3)
    at.sidebar.slider(key="m_slider").set_value(6)
    at.run(timeout=TIMEOUT)
    assert not at.exception and "Schalter ist aus" not in _texts(at)
    at.sidebar.toggle(key="fill_toggle").set_value(True).run(timeout=TIMEOUT)
    assert not at.exception
    assert "**7 Runden**" in _texts(at)
    assert [m.value for m in at.metric][0] == "7"


def test_plan_auswahl_zufall_und_greedy_laufen_ohne_fehler():
    at = _fresh_app()
    for label in ("Zufall", "Greedy (Runde für Runde)", "Suche (Annealing)"):
        at.selectbox(key="view_select").select(label).run(timeout=TIMEOUT)
        assert not at.exception, label
        assert label in " ".join(c.value for c in at.caption)


def test_grosse_feier_ohne_koerper_zeigt_hinweis_statt_plan():
    at = _fresh_app()
    at.sidebar.slider(key="s_slider").set_value(8)
    at.sidebar.slider(key="m_slider").set_value(12)
    at.run(timeout=TIMEOUT)
    assert not at.exception
    assert any("keinen Plan" in i.value for i in at.info)
    at.sidebar.toggle(key="fill_toggle").set_value(True).run(timeout=TIMEOUT)
    assert not at.exception and [m.value for m in at.metric][0] == "13"


def test_exakt_tab_beweist_den_euler_fall():
    at = _fresh_app()
    at.sidebar.slider(key="s_slider").set_value(3)
    at.sidebar.slider(key="m_slider").set_value(6)
    at.run(timeout=TIMEOUT)
    at.number_input(key="exact_w").set_value(6).run(timeout=TIMEOUT)
    at.button(key="exact_start").click().run(timeout=TIMEOUT)
    assert not at.exception
    assert any("Bewiesen: 6 Runden" in e.value for e in at.error)
    at.number_input(key="exact_w").set_value(5).run(timeout=TIMEOUT)
    at.button(key="exact_start").click().run(timeout=TIMEOUT)
    assert any("Es gibt 5 Runden" in s.value for s in at.success)


def test_exakt_tab_bei_zu_vielen_personen():
    at = _fresh_app()  # 48 Personen
    assert any("läuft hier nur bis 24 Personen" in i.value for i in at.info)


def test_permalink_uebernimmt_werte_und_begrenzt_sie():
    at = AppTest.from_file(APP_PATH)
    at.query_params["s"] = "3"
    at.query_params["m"] = "5"
    at.query_params["fill"] = "1"
    at.query_params["budget"] = "99"
    at.run(timeout=TIMEOUT)
    assert not at.exception
    assert at.sidebar.slider(key="s_slider").value == 3 and at.sidebar.slider(key="m_slider").value == 5
    assert at.sidebar.toggle(key="fill_toggle").value is True and at.sidebar.select_slider(key="budget_slider").value == 2  # 99 wird auf 2 begrenzt
