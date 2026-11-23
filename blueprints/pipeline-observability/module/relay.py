from typing import Any, Callable, Dict, List, Optional

from addresses import canonical_address
from observation_state import EGRESS, INGRESS, ObservationState

SOURCE_ENDPOINT_ID = "sensor_feed"
DESTINATION_ENDPOINT_ID = "forward_readings"
SOURCE_ENDPOINT_TYPE = "http_south"
DESTINATION_ENDPOINT_TYPE = "http_north"


def as_celsius_reading(raw: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(raw, dict):
        return None
    asset = raw.get("asset")
    celsius = raw.get("temperature_c")
    if not isinstance(asset, str) or not asset:
        return None
    if isinstance(celsius, bool) or not isinstance(celsius, (int, float)):
        return None
    return {"asset": asset, "temperature_c": celsius, "timestamp": raw.get("timestamp")}


def with_fahrenheit(reading: Dict[str, Any], asset_prefix: str) -> Dict[str, Any]:
    return {
        **reading,
        "asset": asset_prefix + reading["asset"],
        "temperature_f": round(reading["temperature_c"] * 9 / 5 + 32, 2),
    }


class Relay:
    def __init__(
        self,
        state: ObservationState,
        fetch: Callable[[str], List[Any]],
        deliver: Callable[[str, List[Any]], None],
    ) -> None:
        self._state = state
        self._fetch = fetch
        self._deliver = deliver

    def apply_configuration(self, configuration: Dict[str, Any]) -> None:
        source = canonical_address(configuration["source_url"])
        destination = canonical_address(configuration["destination_url"])
        self._state.configure_endpoint(INGRESS, SOURCE_ENDPOINT_ID, SOURCE_ENDPOINT_TYPE, (source,) if source else ())
        self._state.configure_endpoint(EGRESS, DESTINATION_ENDPOINT_ID, DESTINATION_ENDPOINT_TYPE, (destination,) if destination else ())
        if not configuration["enabled"]:
            self._state.set_state(INGRESS, SOURCE_ENDPOINT_ID, "disabled")
            self._state.set_state(EGRESS, DESTINATION_ENDPOINT_ID, "disabled")

    def run_once(self, configuration: Dict[str, Any]) -> None:
        if not configuration["enabled"]:
            return
        raw_readings = self._pull(configuration["source_url"])
        if raw_readings is None:
            return
        converted = self._accept(raw_readings, configuration["egress_asset_prefix"])
        if converted:
            self._push(configuration["destination_url"], converted)

    def _pull(self, source_url: str) -> Optional[List[Any]]:
        try:
            raw_readings = self._fetch(source_url)
        except Exception:
            self._state.set_state(INGRESS, SOURCE_ENDPOINT_ID, "failed")
            return None
        self._state.set_state(INGRESS, SOURCE_ENDPOINT_ID, "running")
        return raw_readings

    def _accept(self, raw_readings: List[Any], asset_prefix: str) -> List[Dict[str, Any]]:
        converted = []
        for raw in raw_readings:
            reading = as_celsius_reading(raw)
            if reading is None:
                self._state.record_discarded()
                continue
            self._state.record_passed(INGRESS, SOURCE_ENDPOINT_ID, reading["asset"])
            converted.append(with_fahrenheit(reading, asset_prefix))
        return converted

    def _push(self, destination_url: str, readings: List[Dict[str, Any]]) -> None:
        try:
            self._deliver(destination_url, readings)
        except Exception:
            self._state.set_state(EGRESS, DESTINATION_ENDPOINT_ID, "failed")
            return
        self._state.set_state(EGRESS, DESTINATION_ENDPOINT_ID, "running")
        for reading in readings:
            self._state.record_passed(EGRESS, DESTINATION_ENDPOINT_ID, reading["asset"])
