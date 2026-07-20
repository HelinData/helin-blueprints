# Helin Platform Starter Pack

A GitHub **template repository** for building and publishing modules to your Helin Platform instance. Create your own repo from this template, fill in the secrets, and go from zero to a published module version in minutes.

This is a starter, not a framework: one correct end-to-end reference path that you grow your own repo from.

## What's inside

```
.
├── scripts/              # helper scripts (M2M token, module registration)
│   ├── get-token.sh      # fetch an M2M access token via client_credentials
│   └── register.sh       # one-time module registration (POST /modules)
├── module/               # your module code (sample built on helin-edge-sdk)
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── .github/workflows/
│   └── publish.yml       # on tag v*: build → push image → publish module version
├── module.yaml           # module metadata; module_id written here after registration
├── Makefile
├── .env.example          # placeholders for local development (no real secrets!)
└── README.md
```

## Quickstart

1. **Create your repo** — click **"Use this template"** on GitHub, then set the six [required secrets](#required-secrets) under *Settings → Secrets and variables → Actions*.
2. **Register your module (once)** — edit `module.yaml` (name, meta_name, author, category_id), then run `make register`. The returned `module_id` is written back into `module.yaml`; commit it.
3. **Publish a version** — push a git tag, e.g. `git tag v1.0.0 && git push origin v1.0.0`. CI builds the container, pushes it to your instance's private registry, and publishes version `1.0.0` of your module.

## Required secrets

Set these as GitHub **Action secrets** on your repository:

| Secret | Description |
| --- | --- |
| `HELIN_CLIENT_ID` | M2M client ID for your platform instance |
| `HELIN_CLIENT_SECRET` | M2M client secret |
| `HELIN_INSTANCE` | Base URL of your platform instance |
| `REGISTRY_URL` | URL of your instance's dedicated private container registry |
| `REGISTRY_USER` | Registry username |
| `REGISTRY_PASSWORD` | Registry password |

For local development, copy `.env.example` to `.env` and fill in the same values. **Never commit real secrets** — `.env` is gitignored.

## How authentication works

Nothing is hardcoded: `scripts/get-token.sh` reads the auth domain and audience from your instance's `/api/v1/configuration/` endpoint, then runs the OAuth2 `client_credentials` grant with `HELIN_CLIENT_ID`/`HELIN_CLIENT_SECRET` and prints an access token.

## Building your own module

The sample in `module/` implements the `helin-edge-sdk` contract (`EdgeModuleRequestsHandler` with `on_get_configuration`, `on_set_configuration`, `on_get_health`) and runs via `EdgeModuleClient.from_edge_environment().run()`. Replace the sample logic with your own — keep the handler contract and the Dockerfile pattern (pinned dependencies, non-root user).
