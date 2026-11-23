from typing import Dict, Iterator

from prometheus_client.metrics_core import Metric

from observation_state import STATES, EndpointRecord, ObservationState

ENDPOINT_READINGS = "edge_endpoint_readings"
ENDPOINT_STATE = "edge_endpoint_state"
ENDPOINT_ADDRESS = "edge_endpoint_address"
ENDPOINT_ASSET = "edge_endpoint_asset"
MODULE_ASSET_READINGS = "edge_module_asset_readings"
MODULE_DISCARDED = "edge_module_discarded"
ADDRESS_LABEL_BY_DIRECTION = {"ingress": "ingress_source", "egress": "egress_destination"}


class ObservationCollector:
    def __init__(self, state: ObservationState, node_id: str, module_id: str) -> None:
        self._state = state
        self._node_id = node_id
        self._module_id = module_id

    def collect(self) -> Iterator[Metric]:
        snapshot = self._state.snapshot()
        yield self._readings(snapshot.endpoints)
        yield self._states(snapshot.endpoints)
        yield self._addresses(snapshot.endpoints)
        yield self._assets(snapshot.endpoints)
        yield self._module_asset_readings(snapshot.module_asset_readings)
        yield self._module_discarded(snapshot.discarded)

    def _module_labels(self) -> Dict[str, str]:
        return {"node_id": self._node_id, "module_id": self._module_id}

    def _endpoint_labels(self, endpoint: EndpointRecord) -> Dict[str, str]:
        direction = endpoint.direction
        labels = {
            **self._module_labels(),
            "direction": direction,
            f"{direction}_id": endpoint.endpoint_id,
            f"{direction}_type": endpoint.endpoint_type,
        }
        if endpoint.addresses:
            labels[ADDRESS_LABEL_BY_DIRECTION[direction]] = endpoint.addresses[0]
        return labels

    def _readings(self, endpoints) -> Metric:
        metric = Metric(ENDPOINT_READINGS, "Readings that passed through the endpoint", "counter")
        for endpoint in endpoints:
            metric.add_sample(ENDPOINT_READINGS + "_total", self._endpoint_labels(endpoint), endpoint.readings)
        return metric

    def _states(self, endpoints) -> Metric:
        metric = Metric(ENDPOINT_STATE, "State of the endpoint", "stateset")
        for endpoint in endpoints:
            for state in STATES:
                labels = {**self._endpoint_labels(endpoint), "state": state}
                metric.add_sample(ENDPOINT_STATE, labels, 1 if state == endpoint.state else 0)
        return metric

    def _addresses(self, endpoints) -> Metric:
        metric = Metric(ENDPOINT_ADDRESS, "The endpoint is reached at, or sends to, this address", "info")
        for endpoint in endpoints:
            for address in endpoint.addresses:
                metric.add_sample(ENDPOINT_ADDRESS + "_info", {**self._endpoint_labels(endpoint), "address": address}, 1)
        return metric

    def _assets(self, endpoints) -> Metric:
        metric = Metric(ENDPOINT_ASSET, "The endpoint has carried readings of this asset", "info")
        for endpoint in endpoints:
            for asset in sorted(endpoint.assets):
                metric.add_sample(ENDPOINT_ASSET + "_info", {**self._endpoint_labels(endpoint), "asset": asset}, 1)
        return metric

    def _module_asset_readings(self, counts: Dict[str, int]) -> Metric:
        metric = Metric(MODULE_ASSET_READINGS, "Readings of this asset the module counted, over all its endpoints", "counter")
        for asset, count in sorted(counts.items()):
            metric.add_sample(MODULE_ASSET_READINGS + "_total", {**self._module_labels(), "asset": asset}, count)
        return metric

    def _module_discarded(self, count: int) -> Metric:
        metric = Metric(MODULE_DISCARDED, "Readings the module dropped without attributing them to an endpoint", "counter")
        metric.add_sample(MODULE_DISCARDED + "_total", self._module_labels(), count)
        return metric
