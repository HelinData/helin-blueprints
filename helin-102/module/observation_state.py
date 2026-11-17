import threading
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

INGRESS = "ingress"
EGRESS = "egress"
STATES = ("running", "failed", "unresponsive", "disabled")


@dataclass
class EndpointRecord:
    direction: str
    endpoint_id: str
    endpoint_type: str
    addresses: Tuple[str, ...] = ()
    state: Optional[str] = None
    readings: int = 0
    assets: set = field(default_factory=set)


@dataclass(frozen=True)
class Snapshot:
    endpoints: List[EndpointRecord]
    module_asset_readings: Dict[str, int]
    discarded: int


class ObservationState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._endpoints: Dict[Tuple[str, str], EndpointRecord] = {}
        self._module_asset_readings: Counter = Counter()
        self._discarded = 0

    def configure_endpoint(self, direction: str, endpoint_id: str, endpoint_type: str, addresses: Tuple[str, ...]) -> None:
        with self._lock:
            record = self._endpoints.setdefault((direction, endpoint_id), EndpointRecord(direction, endpoint_id, endpoint_type))
            record.endpoint_type = endpoint_type
            record.addresses = tuple(addresses)

    def set_state(self, direction: str, endpoint_id: str, state: str) -> None:
        with self._lock:
            self._endpoints[(direction, endpoint_id)].state = state

    def record_passed(self, direction: str, endpoint_id: str, asset: str) -> None:
        with self._lock:
            record = self._endpoints[(direction, endpoint_id)]
            record.readings += 1
            record.assets.add(asset)
            if direction == INGRESS:
                self._module_asset_readings[asset] += 1

    def record_discarded(self) -> None:
        with self._lock:
            self._discarded += 1

    def snapshot(self) -> Snapshot:
        with self._lock:
            endpoints = [
                EndpointRecord(r.direction, r.endpoint_id, r.endpoint_type, r.addresses, r.state, r.readings, set(r.assets))
                for r in self._endpoints.values()
            ]
            return Snapshot(endpoints, dict(self._module_asset_readings), self._discarded)
