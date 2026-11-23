import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from helin_edge_sdk import (
    ConfigurationFailedError,
    EdgeModuleClient,
    EdgeModuleRequestsHandler,
)

CONFIG_PATH = Path(os.getenv("CONFIG_PATH", "/data/configuration.json"))

DEFAULT_CONFIGURATION: dict[str, Any] = {
    "opcua_ip": "123.34.233.1",
    "opcua_port": 4840,
    "poll_interval_ms": 1000,
}


class SampleModule(EdgeModuleRequestsHandler):
    def __init__(self, config_path: Path = CONFIG_PATH) -> None:
        self._config_path = config_path
        self._configuration = self._load()

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
        self._save(configuration)
        self._configuration = configuration
        return {"configuration": configuration}

    def on_get_health(self, payload: dict[str, Any]) -> Any:
        return {"metrics": [{"name": "opcua_connected", "value": 1}]}

    def _load(self) -> dict[str, Any]:
        try:
            loaded = json.loads(self._config_path.read_text())
            if not isinstance(loaded, dict):
                raise ValueError(f"expected a JSON object, got {type(loaded).__name__}")
            return {**DEFAULT_CONFIGURATION, **loaded}
        except FileNotFoundError:
            return dict(DEFAULT_CONFIGURATION)
        except (OSError, ValueError) as exc:
            print(
                f"WARNING: could not load {self._config_path} ({exc}); using defaults",
                file=sys.stderr,
            )
            return dict(DEFAULT_CONFIGURATION)

    def _save(self, configuration: dict[str, Any]) -> None:
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", dir=self._config_path.parent, delete=False
        ) as tmp:
            json.dump(configuration, tmp)
            tmp_path = tmp.name
        os.replace(tmp_path, self._config_path)


if __name__ == "__main__":
    EdgeModuleClient.from_edge_environment(SampleModule()).run()
