"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, Permalink-Umwandlung."""

import trt_constants as C
import trt_evaluation as ev
import trt_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds():
    for name, preset in C.PRESETS.items():
        assert C.S_MIN <= preset["s"] <= C.S_MAX and C.M_MIN <= preset["m"] <= C.M_MAX, name
        assert 0 <= preset["budget"] < len(C.BUDGETS) and 0 <= preset["seed"] <= C.SEED_MAX and isinstance(preset["fill"], bool)


def test_first_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS["Firmenfeier 48"]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_preset_help_mentions_the_numbers_of_its_preset():
    """Die Hilfetexte nennen Abteilungen und Personen je Abteilung des Presets (Namen und Werte dürfen nicht auseinanderlaufen)."""
    for name, preset in C.PRESETS.items():
        text = C.PRESET_HELP[name]
        assert f"{preset['s']} Abteilungen" in text and f"{preset['m']}" in text, name
    assert "Auffüllen" in C.PRESET_HELP["Auffüllen 36"] and C.PRESETS["Auffüllen 36"]["fill"] and not C.PRESETS["Firmenfeier 48"]["fill"]


def test_bool_aus_der_adresszeile():
    assert P._to_bool("1") and P._to_bool("true") and not P._to_bool("0") and not P._to_bool("false") and not P._to_bool("")
