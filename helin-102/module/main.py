import json
import os
import socket
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any

from helin_edge_sdk import (
    ConfigurationFailedError,
    EdgeModuleClient,
    EdgeModuleRequestsHandler,
)
from prometheus_client import CollectorRegistry, start_http_server

from collector import ObservationCollector
from configuration import DEFAULT_CONFIGURATION, validation_errors
from http_transport import fetch_json, post_json
from observation_state import ObservationState
from relay import Relay

CONFIG_PATH = Path(os.getenv("CONFIG_PATH", "/data/configuration.json"))
OBSERVATION_PORT = int(os.getenv("OBSERVATION_PORT", "9600"))


class RelayModule(EdgeModuleRequestsHandler):
    def __init__(self, relay: Relay, state: ObservationState, config_path: Path = CONFIG_PATH) -> None:
        self._relay = relay
        self._state = state
        self._config_path = config_path
        self._configuration = self._load()
        self._relay.apply_configuration(self._configuration)

    @property
    def configuration(self) -> dict[str, Any]:
        return self._configuration

    def on_get_configuration(self, payload: dict[str, Any]) -> Any:
        return self._configuration

    def on_set_configuration(self, payload: dict[str, Any]) -> Any:
        configuration = payload.get("configuration")
        if configuration is None:
            raise ConfigurationFailedError(
                "Missing 'configuration' in payload",
                status_code=400,
                current_configuration=self._configuration,
            )
        errors = validation_errors(configuration)
        if errors:
            raise ConfigurationFailedError(
                "; ".join(errors),
                status_code=400,
                current_configuration=self._configuration,
            )
        self._save(configuration)
        self._configuration = configuration
        self._relay.apply_configuration(configuration)
        return {"configuration": configuration}

    def on_get_health(self, payload: dict[str, Any]) -> Any:
        snapshot = self._state.snapshot()
        return {
            "metrics": [
                {"name": f"{endpoint.direction}_{endpoint.endpoint_id}_readings", "value": endpoint.readings}
                for endpoint in snapshot.endpoints
            ]
            + [{"name": "discarded_readings", "value": snapshot.discarded}]
        }

    def _load(self) -> dict[str, Any]:
        try:
            loaded = json.loads(self._config_path.read_text())
            if not isinstance(loaded, dict):
                raise ValueError(f"expected a JSON object, got {type(loaded).__name__}")
            merged = {**DEFAULT_CONFIGURATION, **loaded}
            if validation_errors(merged):
                raise ValueError("; ".join(validation_errors(merged)))
            return merged
        except FileNotFoundError:
            return dict(DEFAULT_CONFIGURATION)
        except (OSError, ValueError) as exc:
            print(f"WARNING: could not load {self._config_path} ({exc}); using defaults", file=sys.stderr)
            return dict(DEFAULT_CONFIGURATION)

    def _save(self, configuration: dict[str, Any]) -> None:
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", dir=self._config_path.parent, delete=False) as tmp:
            json.dump(configuration, tmp)
            tmp_path = tmp.name
        os.replace(tmp_path, self._config_path)


def serve_observations(state: ObservationState) -> None:
    registry = CollectorRegistry()
    registry.register(
        ObservationCollector(
            state,
            node_id=os.environ.get("IOTEDGE_DEVICEID", socket.gethostname()),
            module_id=os.environ.get("IOTEDGE_MODULEID", "helin-102"),
        )
    )
    start_http_server(OBSERVATION_PORT, registry=registry)


def relay_forever(module: RelayModule, relay: Relay, stop: threading.Event) -> None:
    while True:
        configuration = module.configuration
        relay.run_once(configuration)
        if stop.wait(configuration["poll_interval_s"]):
            return


if __name__ == "__main__":
    observation_state = ObservationState()
    relay = Relay(observation_state, fetch_json, post_json)
    module = RelayModule(relay, observation_state)
    serve_observations(observation_state)
    stop = threading.Event()
    threading.Thread(target=relay_forever, args=(module, relay, stop), daemon=True).start()
    EdgeModuleClient.from_edge_environment(module).run()
    stop.set()
