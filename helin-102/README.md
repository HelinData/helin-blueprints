# helin-102: integrating a module with data pipeline observability

This example shows how a custom module becomes visible in the **Data pipelines** graph of the Helin Platform (the data pipeline observability, "DPO"). It is a sibling of the Module Starter Pack in the repository root and uses the same registration and publishing flow.

The module is a small relay: it polls an HTTP source for temperature readings in Celsius, adds a Fahrenheit value, and forwards them to an HTTP destination. The relay is deliberately simple. The point of the example is `module/collector.py`, which exposes the same observations the Helin Data Collector (HDC) exposes.

## How the platform sees a module

The platform does not ask modules about their pipelines. Every module reports **observations**: Prometheus metrics on an HTTP endpoint, port `9600`, path `/metrics`. The node's metrics collector scrapes that endpoint every 300 seconds and uploads it to the instance's Log Analytics workspace. The platform builds the graph and each connection's status from those observations. A module reports facts, never a status.

HDC (`hdc_observer`, from HDC v31.4) is the reference implementation. This module reproduces its exposition exactly, so the platform treats it like any other module and links it to HDC modules.

## The observation contract

Every endpoint (a connection data enters or leaves through) carries these labels:

| Label | Presence | Value in this module |
| --- | --- | --- |
| `node_id` | required | `IOTEDGE_DEVICEID` |
| `module_id` | required | `IOTEDGE_MODULEID` |
| `direction` | required | `ingress` or `egress` |
| `ingress_id`, `ingress_type` | when `ingress` | `sensor_feed`, `http_south` |
| `ingress_source` | optional | canonical address the ingress reads from |
| `egress_id`, `egress_type` | when `egress` | `forward_readings`, `http_north` |
| `egress_destination` | optional | canonical address the egress writes to |

The module exposes the six families HDC exposes:

| Metric | Kind | Extra labels | Meaning |
| --- | --- | --- | --- |
| `edge_endpoint_readings_total` | counter | endpoint labels | Readings that passed through the endpoint |
| `edge_endpoint_state` | state set | endpoint labels, `state` | One of `running`, `failed`, `unresponsive`, `disabled` is 1 |
| `edge_endpoint_address_info` | info, always 1 | endpoint labels, `address` | An address the endpoint reads from, is reached at or writes to |
| `edge_endpoint_asset_info` | info, always 1 | endpoint labels, `asset` | The endpoint has carried readings of this asset |
| `edge_module_asset_readings_total` | counter | `node_id`, `module_id`, `asset` | Readings of this asset the module counted over all its endpoints |
| `edge_module_discarded_total` | counter | `node_id`, `module_id` | Readings dropped without attributing them to an endpoint |

Rules the example follows:

- An endpoint id is its configured name, stable across restarts and unique within the module.
- An endpoint type is `<protocol>_<south|north>`.
- Report only the endpoints configured now.
- `asset` is the asset name as the endpoint hands readings on: the name after the ingress's own transformations, the name sent by the egress.
- Never put credentials in a label. Addresses carry scheme, host, port and path only.
- Never emit a derived status such as "flowing". The platform derives it.

## How the graph is built from the labels

| Link | Rule | In this module |
| --- | --- | --- |
| Inside a module | An egress links to every ingress with an endpoint asset observation of the same `asset`. A renamed asset gets an opaque link from every ingress. | Set `egress_asset_prefix` to rename assets and see the opaque link |
| Between modules or nodes | An egress links to an ingress when `egress_destination` equals an address the ingress reports | Point `destination_url` at an HDC `http_south` address |
| Module-local | `iotedge://` and `generated://` addresses | Not used here |

Addresses are compared as strings, so they use one canonical form (`module/addresses.py`): lowercase scheme and host, explicit port (default ports included), no trailing slash, no user info, query or fragment, and the host exactly as the client dials it.

To see this module feed an HDC datasink, set `destination_url` to the address the HDC `http_south` reports, for example `https://<traffic-manager-fqdn>:6684/sensor-reading`, byte for byte in canonical form.

## Status the platform derives

| Status | Derived from |
| --- | --- |
| Not connected | IoT Hub reports the node disconnected |
| Error | `edge_endpoint_state` is `failed` or `unresponsive` |
| Disabled | `edge_endpoint_state` is `disabled` |
| Flowing | `edge_endpoint_readings_total` increased within the time window |
| Stale | enabled and connected, but no increase within the time window |
| Not observed | the node is connected but the module exposes nothing |

In this module `sensor_feed` is `failed` when the source cannot be reached, `forward_readings` is `failed` when the destination rejects a delivery, and both are `disabled` when `enabled` is `false`.

## Layout

```
helin-102/
├── module.yaml            module metadata for `make register` (meta_name: helin-102)
├── module_metadata.json   deploy-time templates; exposes port 9600
├── Makefile               test, build, register, publish
├── .env.example           credentials for register and publish
├── scripts/               get-token, register, publish-version, build-and-publish
├── README.md
└── module/
    ├── main.py            SDK handler, relay loop, observation server on port 9600
    ├── collector.py       the six observation families
    ├── observation_state.py  thread-safe counters, states and assets the collector reads
    ├── addresses.py       canonical, credential-free addresses
    ├── relay.py           the example logic: poll, convert, forward, record observations
    ├── configuration.py   defaults and validation
    ├── http_transport.py  HTTP fetch and post
    ├── Dockerfile
    ├── pyproject.toml
    ├── poetry.lock
    └── tests/
```

To reuse the example in your own module, keep `collector.py`, `observation_state.py` and `addresses.py`, and call `ObservationState` from your own logic: `configure_endpoint` once per endpoint and whenever its address changes, `set_state` on every state change, `record_passed` for every reading that passes an endpoint, and `record_discarded` for readings you drop.

## Configuration

| Key | Default | Meaning |
| --- | --- | --- |
| `enabled` | `true` | `false` stops polling and reports both endpoints `disabled` |
| `source_url` | `http://sensor-gateway.local:8080/readings` | HTTP endpoint returning a JSON list of `{"asset": str, "temperature_c": number, "timestamp": any}` |
| `destination_url` | `https://datasink.example.com:6684/sensor-reading` | HTTP endpoint receiving the converted list by POST |
| `poll_interval_s` | `10` | Seconds between polls |
| `egress_asset_prefix` | empty | Prepended to the asset name on the way out |

Entries without a string `asset` or a numeric `temperature_c` are discarded and counted in `edge_module_discarded_total`.

## Deploy it

This folder is self-contained: everything below runs from `helin-102/`. You need a Helin Platform instance with M2M credentials and the instance's private container registry, Docker with buildx, `jq`, `curl` and Poetry.

1. **Credentials.** Copy `.env.example` to `.env` and fill in the six values (`HELIN_INSTANCE`, `HELIN_CLIENT_ID`, `HELIN_CLIENT_SECRET`, `REGISTRY_URL`, `REGISTRY_USER`, `REGISTRY_PASSWORD`). `.env` is gitignored.
2. **Check it.** `make test` runs the unit tests. `make build` builds the image locally.
3. **Register the module once.** Edit `module.yaml` (`name`, `author`, `category_id`), then run `make register`. It writes `module_id` and `module_uuid` back into `module.yaml`. Keep `meta_name: helin-102` unless you rename the module, because the later steps depend on it.
4. **Publish a version.** `make publish VERSION=1.0.0` logs in to your registry, builds and pushes `$REGISTRY_URL/helin-102:1.0.0` for amd64, arm64 and arm/v7 (override with `PLATFORMS`), and publishes version `1.0.0` using `module_metadata.json`.
5. **Add the module to a template.** In the Portal, add `helin-102` to the template of the nodes that should run it and set its configuration (`source_url`, `destination_url`).
6. **Make the platform scrape it.** In the same template, add `helin-102:9600` to the metrics collector bindings. The name before the port is the module's `meta_name`: the platform uses it as the module name in the node's deployment, so the metrics collector reaches the module under that name, and the same name becomes the `module_id` label. Without this binding the module runs but the Data pipelines page shows **Not observed**. HDC has the same setup, bound as `HelinDataCollector:9600`.
7. **Deploy the template** to the node. The node starts reporting after the deployment, and the module appears in **Data pipelines** within about ten minutes, because modules report every five minutes.

The CI workflows of the repository root are not part of this folder. Run `make publish` locally, or call `scripts/build-and-publish.sh` from your own pipeline.

## Verify

- On the node, `docker exec` into the module and fetch `http://localhost:9600/metrics`. You should see the six `edge_*` families with your `node_id` and `module_id=helin-102`.
- In the Portal, open **Data pipelines**, then **Node detail**, select the node and the module. `sensor_feed` and `forward_readings` show **Flowing** once readings pass within the selected time window.
- Point `destination_url` at an HDC `http_south` address and the graph links the two modules.

## References

- Data pipelines (Platform documentation): `products/reference-docs/data-pipelines.md` in `helin-platform-docs`
- ADR 0007, data pipeline observability through module-emitted observations (`POLARIS-Ursa-Minor.Api`)
- `hdc_observer` in `HELIN-Data-Collector` (`python/hdc_observer`)
