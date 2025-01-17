# FAIR MAST Data Management System

## Development Setup

### Mac Users

If you are using Mac for development, use [podman](https://podman.io/docs/installation) instead of docker. Follow the installation guide to set it up, then follow the below set up. Also install ``podman-mac-helper``, which provides a compatibility layer that allows you to use most Docker commands with Podman on macOS.

### Linux/Windows Users

If using Linux or Windows, you need to make sure you have [docker](https://www.docker.com/get-started/) and `docker-compose` installed on your system.

### Setup

Secondly, clone the repository:

```bash
git clone git@github.com:ukaea/fair-mast.git
cd fair-mast
```

### Start the Data Management System

Run the development container to start the postgres database, fastapi, and minio containers locally. The development environment will watch the source directory and automatically reload changes to the API as you work.

#### Mac Users

```bash
podman compose \
--env-file dev/docker/.env.dev  \
-f dev/docker/docker-compose.yml \
up \
--build
```

Podman does not shutdown containers on its own, unlike Docker. To shutdown Podman completely run:

```bash
podman compose -f dev/docker/docker-compose.yml down   
podman volume rm --all
```

#### Linux/Windows Users

```bash
docker-compose \
--env-file dev/docker/.env.dev  \
-f dev/docker/docker-compose.yml \
up \
--build
```

The following services will be started:

- FastAPI REST & GraphQL Server - will start running at `http://localhost:8081`.
  - The REST API documentation is at `http://localhost:8081/redoc`.
  - The GraphQL API documentation is at `http://localhost:8081/graphql`.
- Postgres Database Server - will start running at `http://localhost:5432`
- Postgres Admin Server - will start running at `http://localhost:5050`

### Populate the Database

To create the database and populate it with content we need to get the metadata files. These are stored in the repository using [Git LFS](https://git-lfs.com).

To retrieve these data files, follow the below instructions in your terminal:

```bash
git lfs install
git lfs fetch
git lfs pull
```

Assuming the files have been pulled successfully, the data files should exist within `tests/mock_data/mini` in the local directory. We can
create the database and ingest data using the following command:

#### Mac Users

```bash
podman exec -it mast-api python -m src.api.create /code/data/index
```

#### Linux/Windows Users

```bash
docker exec -it mast-api python -m src.api.create /code/data/index
```

### Running Unit Tests

Verify everything is setup correctly by running the unit tests.

Follow the below instructions to set up the environment.

```bash
uv run pytest
```

## Production Deployment

To run the production container to start the postgres database, fastapi, and minio containers. This will also start an nginx proxy and make sure https is all setup

```bash
docker compose --env-file dev/docker/.env.dev  -f dev/docker/docker-compose.yml -f dev/docker/docker-compose-prod.yml up --build --force-recreate --remove-orphans -d
```

To shut down the production deployment, run the following command:

```bash
docker compose --env-file dev/docker/.env.dev  -f dev/docker/docker-compose.yml -f dev/docker/docker-compose-prod.yml down
```

To also destory the volumes (including the metadatabase) you may add the volumes parameter:

```bash
docker compose --env-file dev/docker/.env.dev  -f dev/docker/docker-compose.yml -f dev/docker/docker-compose-prod.yml down --volumes
```

**Note:** Every time you destory volumes, the production server will mint a new certificate for HTTPS. Lets Encrypt currently limits this to [5 per week](https://letsencrypt.org/docs/duplicate-certificate-limit/).

You'll need to download and ingest the production data like so:

```bash
mkdir -p data/mast/meta
rsync -vaP <CSD3-USERNAME>@login.hpc.cam.ac.uk:/rds/project/rds-sPGbyCAPsJI/archive/metadata data/
```

```bash
docker exec -it mast-api python -m src.api.create /code/data/index
```

## Building Documentation

See the guide to building documentation [here](./docs/README.md)
