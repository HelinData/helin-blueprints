# Helin Blueprints

Working, deployable reference solutions for the Helin Platform. Each blueprint solves one integration problem end to end: the module code, its tests, the deploy-time metadata, and the steps to register, publish and deploy it to a node.

This catalog is for customers, implementation partners and forward deployed engineers. Find the blueprint that matches your problem, copy its folder into a repository of your own, and adapt it.

## Find a blueprint

| Blueprint | Solves | Builds on |
| --- | --- | --- |
| [module-starter](blueprints/module-starter/) | Build, register and publish a custom edge module, with CI that publishes a version on every git tag | - |
| [pipeline-observability](blueprints/pipeline-observability/) | Make a custom module visible, with live status, in the **Data pipelines** graph, linked to HDC modules | module-starter |

Not sure where to start? Begin with **module-starter**. Every other blueprint uses its registration and publishing flow.

## Use a blueprint

1. Read the blueprint's README. It states when to use the blueprint, how it works and what you need.
2. Copy the blueprint folder to the root of a new repository, including `.github/` and the dotfiles where present.
3. Follow the blueprint's deploy steps: credentials in `.env`, `make register` once, then publish a version.

Every blueprint is self-contained. It does not depend on files outside its own folder, so a copy keeps working.

## What every blueprint contains

```
blueprints/<name>/
├── README.md             when to use it, how it works, deploy and verify steps
├── module.yaml           module metadata for `make register`
├── module_metadata.json  deploy-time templates sent with every published version
├── Makefile              register, build, publish (and test where present)
├── .env.example          credentials for local register and publish
├── .gitignore
├── scripts/              get-token, register, publish-version
└── module/               module code, Dockerfile, pyproject.toml, poetry.lock, tests/
```

## Add a blueprint

1. Start from a copy of `blueprints/module-starter/` under a descriptive, lowercase-with-dashes name that names the problem, not the ticket.
2. Use the folder name as `meta_name` in `module.yaml` and as the image name, and give the data volume in `module_metadata.json` a name unique to the blueprint.
3. Open the README with a **Use this blueprint when** line, and end it with deploy and verify steps that run from the blueprint folder.
4. Add unit tests in `module/tests/`. CI runs them and builds the image for amd64, arm64 and arm/v7 for every folder under `blueprints/` that has a `module/`.
5. Add a row to the table in [Find a blueprint](#find-a-blueprint).
