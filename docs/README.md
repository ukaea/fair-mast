# FAIR MAST Documentation

Example notebooks and documentation for using the MAST data archive. See the [live documentation](https://mastapp.site/).

To build the documentation locally, create its dedicated virtual environment (kept separate from the application's dependencies) and run Jupyter Book from the repository root:

```bash
uv venv .docs-venv --python 3.12
source .docs-venv/bin/activate
uv pip install -r docs-requirements.txt
jb build docs --path-output docs/built_docs
```

Notebook execution is cached: only notebooks whose source has changed are re-run,
and the rest reuse cached outputs under `docs/built_docs/_build/.jupyter_cache`.
Delete that directory to force a full re-execution against the live API and
object store.

Then (re)start the docker containers to serve the built docs:

```bash
docker compose --env-file dev/docker/.env.dev -f dev/docker/docker-compose.yml up --remove-orphans --build --force-recreate -d
```
