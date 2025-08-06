# FAIR MAST Documentation
By default the full documentation isn't built when cloing this repository, only the folloing instructions are served on localhost:8081:

In order to build the documentation simply run the following command from the base folder:

```bash
uv run jb build docs --path-output docs/built_docs
```

Once it has finished running simply restart (or run for the first time) the docker containers using:

```bash
docker compose --env-file dev/docker/.env.dev  -f dev/docker/docker-compose.yml up --remove-orphans --build --force-recreate -d
```

Or equivalent

Example notebooks and documentation for using the MAST data archive. See a live version of this documentations [here](https://mastapp.site/)