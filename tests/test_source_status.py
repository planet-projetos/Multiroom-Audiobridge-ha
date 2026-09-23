import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from custom_components.audiobridge import config_flow

MODULE_PATH = Path(__file__).resolve().parents[1] / "custom_components" / "audiobridge" / "audiobridge_api.py"
MODULE_SPEC = importlib.util.spec_from_file_location("audiobridge_api_under_test", MODULE_PATH)
MODULE = importlib.util.module_from_spec(MODULE_SPEC)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
MODULE_SPEC.loader.exec_module(MODULE)
parse_zone_status_response = MODULE.parse_zone_status_response


def test_names_schema_includes_zone_and_source_fields():
    schema = config_flow._names_schema()

    assert "zone_1_name" in schema.schema
    assert "source_1_name" in schema.schema
    assert "zone_8_name" in schema.schema
    assert "source_8_name" in schema.schema


def test_parse_zone_status_response_reads_source_from_ch_field():
    payload = "< 11PT00PR01MU00VO09CH03"

    data = parse_zone_status_response(payload)

    assert data["source"] == 3
    assert data["power"] is True
    assert data["mute"] is False
    assert data["volume"] == 9


def test_parse_zone_status_response_keeps_previous_source_when_ch_missing():
    payload = "< 11PT00PR01MU00VO09"
    previous = {"source": 5, "power": True, "mute": False, "volume": 9}

    data = parse_zone_status_response(payload, previous_source=previous.get("source"))

    assert data["source"] == 5
    assert data["power"] is True
    assert data["volume"] == 9
