from prometheus_client import CollectorRegistry
from prometheus_client.exposition import generate_latest

from collector import ObservationCollector
from configuration import DEFAULT_CONFIGURATION
from observation_state import EGRESS, INGRESS, ObservationState
from relay import Relay


def exposition_after_one_poll(readings, **overrides):
    state = ObservationState()
    relay = Relay(state, lambda url: readings, lambda url, payload: None)
    configuration = {**DEFAULT_CONFIGURATION, "source_url": "http://Sensor-Gateway.local:8080/readings/", **overrides}
    relay.apply_configuration(configuration)
    relay.run_once(configuration)
    registry = CollectorRegistry()
    registry.register(ObservationCollector(state, node_id="vessel-x", module_id="helin-102"))
    return registry, generate_latest(registry).decode()


def samples(registry, name):
    return [s for metric in registry.collect() for s in metric.samples if s.name == name]


def test_all_six_observation_families_are_exposed():
    _, text = exposition_after_one_poll([{"asset": "boiler_1", "temperature_c": 20}])
    for family in (
        "edge_endpoint_readings_total",
        "edge_endpoint_state",
        "edge_endpoint_address_info",
        "edge_endpoint_asset_info",
        "edge_module_asset_readings_total",
        "edge_module_discarded_total",
    ):
        assert family in text


def test_ingress_endpoint_carries_the_required_labels_and_its_canonical_source():
    registry, _ = exposition_after_one_poll([{"asset": "boiler_1", "temperature_c": 20}])
    ingress = next(s for s in samples(registry, "edge_endpoint_readings_total") if s.labels["direction"] == INGRESS)
    assert ingress.labels == {
        "node_id": "vessel-x",
        "module_id": "helin-102",
        "direction": "ingress",
        "ingress_id": "sensor_feed",
        "ingress_type": "http_south",
        "ingress_source": "http://sensor-gateway.local:8080/readings",
    }
    assert ingress.value == 1


def test_egress_endpoint_carries_the_required_labels_and_its_canonical_destination():
    registry, _ = exposition_after_one_poll([{"asset": "boiler_1", "temperature_c": 20}])
    egress = next(s for s in samples(registry, "edge_endpoint_readings_total") if s.labels["direction"] == EGRESS)
    assert egress.labels["egress_id"] == "forward_readings"
    assert egress.labels["egress_type"] == "http_north"
    assert egress.labels["egress_destination"] == "https://datasink.example.com:6684/sensor-reading"


def test_state_set_has_one_active_state_per_endpoint():
    registry, _ = exposition_after_one_poll([{"asset": "boiler_1", "temperature_c": 20}])
    active = [(s.labels["direction"], s.labels["state"]) for s in samples(registry, "edge_endpoint_state") if s.value == 1]
    assert sorted(active) == [("egress", "running"), ("ingress", "running")]
    assert len(samples(registry, "edge_endpoint_state")) == 8


def test_endpoint_asset_and_address_info_values_are_always_one():
    registry, _ = exposition_after_one_poll([{"asset": "boiler_1", "temperature_c": 20}])
    assert {s.value for s in samples(registry, "edge_endpoint_asset_info")} == {1}
    assert {s.value for s in samples(registry, "edge_endpoint_address_info")} == {1}
    assert {s.labels["asset"] for s in samples(registry, "edge_endpoint_asset_info")} == {"boiler_1"}


def test_renamed_egress_asset_is_reported_as_the_name_that_leaves_the_module():
    registry, _ = exposition_after_one_poll([{"asset": "boiler_1", "temperature_c": 20}], egress_asset_prefix="site_a.")
    assets = {(s.labels["direction"], s.labels["asset"]) for s in samples(registry, "edge_endpoint_asset_info")}
    assert assets == {("ingress", "boiler_1"), ("egress", "site_a.boiler_1")}


def test_module_level_families_carry_only_node_module_and_asset_labels():
    registry, _ = exposition_after_one_poll([{"asset": "boiler_1", "temperature_c": 20}, {"nope": 1}])
    [per_asset] = samples(registry, "edge_module_asset_readings_total")
    assert per_asset.labels == {"node_id": "vessel-x", "module_id": "helin-102", "asset": "boiler_1"}
    [discarded] = samples(registry, "edge_module_discarded_total")
    assert discarded.labels == {"node_id": "vessel-x", "module_id": "helin-102"}
    assert discarded.value == 1


def test_no_label_value_carries_credentials():
    _, text = exposition_after_one_poll(
        [{"asset": "boiler_1", "temperature_c": 20}],
        source_url="http://user:secret@sensor-gateway.local:8080/readings?token=abc",
        destination_url="https://user:secret@datasink.example.com:6684/in?sig=abc",
    )
    for leaked in ("secret", "user:", "token=", "sig="):
        assert leaked not in text


def test_counter_line_matches_the_format_hdc_exposes_on_its_metrics_port():
    _, text = exposition_after_one_poll([{"asset": "boiler_1", "temperature_c": 20}])
    assert "# TYPE edge_endpoint_readings_total counter" in text
    assert (
        'edge_endpoint_readings_total{direction="ingress",ingress_id="sensor_feed",'
        'ingress_source="http://sensor-gateway.local:8080/readings",ingress_type="http_south",'
        'module_id="helin-102",node_id="vessel-x"} 1.0'
    ) in text
