import pytest

from configuration import DEFAULT_CONFIGURATION, validation_errors


def test_default_configuration_is_valid():
    assert validation_errors(DEFAULT_CONFIGURATION) == []


@pytest.mark.parametrize(
    "key, value",
    [
        ("enabled", "yes"),
        ("source_url", "ftp://host/file"),
        ("destination_url", ""),
        ("poll_interval_s", 0),
        ("poll_interval_s", True),
        ("egress_asset_prefix", 5),
    ],
)
def test_invalid_value_is_reported(key, value):
    assert validation_errors({**DEFAULT_CONFIGURATION, key: value}) != []


def test_missing_keys_are_reported():
    assert len(validation_errors({})) == 5
