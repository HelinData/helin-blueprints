import pytest

from configuration import DEFAULT_CONFIGURATION
from observation_state import EGRESS, INGRESS, ObservationState
from relay import DESTINATION_ENDPOINT_ID, SOURCE_ENDPOINT_ID, Relay


class FakeNetwork:
    def __init__(self, readings=None, source_error=None, destination_error=None):
        self.readings = readings or []
        self.source_error = source_error
        self.destination_error = destination_error
        self.delivered = []

    def fetch(self, url):
        if self.source_error:
            raise self.source_error
        return self.readings

    def deliver(self, url, readings):
        if self.destination_error:
            raise self.destination_error
        self.delivered.append((url, readings))


def build(network, **overrides):
    state = ObservationState()
    relay = Relay(state, network.fetch, network.deliver)
    configuration = {**DEFAULT_CONFIGURATION, **overrides}
    relay.apply_configuration(configuration)
    return state, relay, configuration


def endpoint(state, direction):
    return next(e for e in state.snapshot().endpoints if e.direction == direction)


def test_readings_are_converted_to_fahrenheit_and_forwarded():
    network = FakeNetwork([{"asset": "boiler_1", "temperature_c": 100, "timestamp": "t1"}])
    _, relay, configuration = build(network)
    relay.run_once(configuration)
    assert network.delivered == [
        (configuration["destination_url"], [{"asset": "boiler_1", "temperature_c": 100, "timestamp": "t1", "temperature_f": 212.0}])
    ]


def test_both_endpoints_count_the_readings_that_passed_and_the_assets_they_carried():
    network = FakeNetwork([{"asset": "boiler_1", "temperature_c": 20}, {"asset": "boiler_2", "temperature_c": 30}])
    state, relay, configuration = build(network)
    relay.run_once(configuration)
    for direction in (INGRESS, EGRESS):
        record = endpoint(state, direction)
        assert record.readings == 2
        assert record.assets == {"boiler_1", "boiler_2"}
        assert record.state == "running"


def test_module_counts_ingested_readings_per_asset_once_over_all_endpoints():
    network = FakeNetwork([{"asset": "boiler_1", "temperature_c": 1}, {"asset": "boiler_1", "temperature_c": 2}])
    state, relay, configuration = build(network)
    relay.run_once(configuration)
    assert state.snapshot().module_asset_readings == {"boiler_1": 2}


def test_egress_asset_prefix_renames_only_the_forwarded_assets():
    network = FakeNetwork([{"asset": "boiler_1", "temperature_c": 1}])
    state, relay, configuration = build(network, egress_asset_prefix="site_a.")
    relay.run_once(configuration)
    assert endpoint(state, INGRESS).assets == {"boiler_1"}
    assert endpoint(state, EGRESS).assets == {"site_a.boiler_1"}


@pytest.mark.parametrize(
    "malformed",
    [None, "text", {}, {"asset": "", "temperature_c": 1}, {"asset": "a"}, {"asset": "a", "temperature_c": "hot"}, {"asset": "a", "temperature_c": True}],
)
def test_malformed_readings_are_discarded_without_touching_any_endpoint(malformed):
    network = FakeNetwork([malformed])
    state, relay, configuration = build(network)
    relay.run_once(configuration)
    snapshot = state.snapshot()
    assert snapshot.discarded == 1
    assert [e.readings for e in snapshot.endpoints] == [0, 0]
    assert network.delivered == []


def test_unreachable_source_marks_the_ingress_failed_and_forwards_nothing():
    network = FakeNetwork(source_error=OSError("down"))
    state, relay, configuration = build(network)
    relay.run_once(configuration)
    assert endpoint(state, INGRESS).state == "failed"
    assert endpoint(state, EGRESS).state is None
    assert network.delivered == []


def test_rejecting_destination_marks_the_egress_failed_and_counts_no_egress_readings():
    network = FakeNetwork([{"asset": "a", "temperature_c": 1}], destination_error=OSError("refused"))
    state, relay, configuration = build(network)
    relay.run_once(configuration)
    assert endpoint(state, INGRESS).state == "running"
    assert endpoint(state, INGRESS).readings == 1
    assert endpoint(state, EGRESS).state == "failed"
    assert endpoint(state, EGRESS).readings == 0


def test_disabled_module_reports_both_endpoints_disabled_and_does_not_poll():
    network = FakeNetwork([{"asset": "a", "temperature_c": 1}])
    state, relay, configuration = build(network, enabled=False)
    relay.run_once(configuration)
    assert [e.state for e in state.snapshot().endpoints] == ["disabled", "disabled"]
    assert network.delivered == []


def test_reconfiguring_changes_addresses_but_keeps_counters():
    network = FakeNetwork([{"asset": "a", "temperature_c": 1}])
    state, relay, configuration = build(network)
    relay.run_once(configuration)
    relay.apply_configuration({**configuration, "destination_url": "https://other.example.com:6684/in"})
    egress = endpoint(state, EGRESS)
    assert egress.addresses == ("https://other.example.com:6684/in",)
    assert egress.readings == 1


def test_endpoint_ids_are_stable():
    state, _, _ = build(FakeNetwork())
    assert [e.endpoint_id for e in state.snapshot().endpoints] == [SOURCE_ENDPOINT_ID, DESTINATION_ENDPOINT_ID]
