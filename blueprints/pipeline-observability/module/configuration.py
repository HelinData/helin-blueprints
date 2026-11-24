from typing import Any, Dict, List

from addresses import canonical_address

DEFAULT_CONFIGURATION: Dict[str, Any] = {
    "enabled": True,
    "source_url": "http://sensor-gateway.local:8080/readings",
    "destination_url": "https://datasink.example.com:6684/sensor-reading",
    "poll_interval_s": 10,
    "egress_asset_prefix": "",
}


def validation_errors(configuration: Dict[str, Any]) -> List[str]:
    errors = []
    if not isinstance(configuration.get("enabled"), bool):
        errors.append("enabled must be true or false")
    for key in ("source_url", "destination_url"):
        value = configuration.get(key)
        if not isinstance(value, str) or canonical_address(value) is None:
            errors.append(f"{key} must be an http or https URL")
    interval = configuration.get("poll_interval_s")
    if not isinstance(interval, int) or isinstance(interval, bool) or interval < 1:
        errors.append("poll_interval_s must be a positive integer")
    if not isinstance(configuration.get("egress_asset_prefix"), str):
        errors.append("egress_asset_prefix must be a string")
    return errors
