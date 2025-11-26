from __future__ import annotations

from pathlib import Path

import xmltodict

from custom_components.ventilation_system import parser
from custom_components.ventilation_system.sensor import SENSORS


def load_fixture() -> dict[str, str]:
    fixture = Path("tests/fixtures/status.xml").read_text(encoding="utf-8")
    return xmltodict.parse(fixture)["response"]


def test_value_as_text_handles_structured_inputs() -> None:
    assert parser.value_as_text(" Auto: Zu   ") == "Auto: Zu"
    assert parser.value_as_text({"#text": " 12 "}) == "12"
    assert parser.value_as_text({"value": {"#text": "33"}}) == "33"
    assert parser.value_as_text(["", {"#text": "abc "}]) == "abc"
    assert parser.value_as_text(None) is None


def test_numeric_helpers_extract_numbers() -> None:
    assert parser.extract_number(" 13,5 °C") == "13,5"
    assert parser.extract_number({"value": {"#text": "33"}}) == "33"
    assert parser.extract_number("foo") is None


def test_as_float_and_int() -> None:
    assert parser.as_float(" 13,5 °C") == 13.5
    assert parser.as_float({"#text": "38"}) == 38.0
    assert parser.as_int(" 15 Tage") == 15
    assert parser.as_int({"value": {"#text": "33"}}) == 33


def test_stage_value_parsing() -> None:
    assert parser.stage_value("Stufe3 Abwesend") == 3
    assert parser.stage_value("2") == 2
    assert parser.stage_value(None) is None


def test_sensor_descriptions_parse_fixture() -> None:
    data = load_fixture()
    values = {description.key: description.value_from(data) for description in SENSORS}

    assert values["aktuell0"] == 2
    assert values["control0"] == "manuelle Stufenwahl"
    assert values["bypass"] == "Auto: Zu"
    assert values["rest_time"] == 0
    assert values["filtertime"] == 180
    assert values["BipaAutAUL"] == 13.0
    assert values["BipaAutABL"] == 23.0
