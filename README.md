# FAIR MAST Data Management System

## Overview


## Development Setup

### Mac Users:

If you are using Mac for development, use [podman](https://podman.io/docs/installation) instead of docker. Follow the installation guide to set it up, then follow the below set up. 

### Linux/Windows Users:

If using Linux or Windows, you need to make sure you have [docker](https://www.docker.com/get-started/) and `docker-compose` installed on your system.

### Setup

We will be using the Python package manager [uv](https://astral.sh/blog/uv) to install our dependencies. As a first step, make sure this is installed with:
```bash
pip install uv
```
Secondly, clone the repository:
```bash
git clone git@github.com:ukaea/fair-mast.git
cd fair-mast
```

You can use either `conda` or `venv` to set up the environment. Follow the below instructions depending on your preference. 
### Option 1: Using Conda
Assuming you already have conda installed on your system:
```bash
conda create -n mast python=3.11
conda activate mast
uv pip install -r docs/requirements.txt
```

### Option 2: Using venv
Ensure you are using Python version `3.11`:
```bash
uv venv venv
source venv/bin/activate
uv pip install -r docs/requirements.txt
```

Use `uv --help` for additional commands, or refer to the documentation if needed.

### Start the Data Management System
Run the development container to start the postgres database, fastapi, and minio containers locally. The development environment will watch the source directory and automatically reload changes to the API as you work.

### Mac Users:

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

### Linux/Windows Users:

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
 - Postgres Admin Server - will start running at `http://localhost:8081/pgadmin`
 - Minio S3 Storage Server - will start running at `http://localhost:9000`.
    - The admin web GUI will be running at `http://localhost:8081/minio/ui`. 

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

### Mac Users:

```bash
podman exec -it mast-api python -m src.api.create /code/data/mini
```

### Linux/Windows Users:

```bash
docker exec -it mast-api python -m src.api.create /code/data/mini
```

### Running Unit Tests
Verify everything is setup correctly by running the unit tests.

To run the unit tests, input the following command inside your environment:

```bash
python -m pytest -rsx tests/ --data-path="INSERT FULL PATH TO DATA HERE"
```

The data path will be will be along the lines of `~/fair-mast/tests/mock_data/mini`.

This will run some unit tests for the REST and GraphQL APIs against a testing database, created from the data in `--data-path`. 

### Uploading Data to the Minio Storage

First, follow the [instructions to install the minio client](https://min.io/docs/minio/linux/reference/minio-mc.html) tool.

Next, configure the endpoint location. The development minio installation runs at `localhost:9000` and has the following default username and password for development:

```bash
mc alias set srv http://localhost:9000 minio99 minio123;
```

Then you can copy data to the bucket using:

```bash
mc cp --recursive <path-to-data> srv/mast
```


### Production Deployment

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

**Note** that every time you destory volumes, the production server will mint a new certificate for HTTPS. Lets Encrypt currently limits this to [5 per week](https://letsencrypt.org/docs/duplicate-certificate-limit/)

You'll need to ingest download and ingest the production data like so:

```bash
mkdir -p data/mast/meta
rsync -vaP <CSD3-USERNAME>@login.hpc.cam.ac.uk:/rds/project/rds-sPGbyCAPsJI/archive/metadata data/
```

```bash
docker exec -it mast-api python -m src.api.create /code/data/index
```

## Building Documentation

See the guide to building documentation [here](./docs/README.md)

## Ingestion to S3

The following section details how to ingest data into the s3 storage on freia with UDA.

1. SSH onto freia and setup a local development environment following the instuctions above.
2. Parse the metadata for all signals and sources for a list of shots with the following command

```sh
mpirun -n 16 python3 -m src.archive.create_uda_metadata data/uda campaign_shots/tiny_campaign.csv 
```

This will create the metadata for the tiny campaign. You may do the same for full campaigns such as `M9`.

3. Run the ingestion pipleline by submitting the following job:

```sh
qsub ./jobs/freia_write_datasets.qsub campaign_shots/tiny_campaign.csv s3://mast/level1/shots
```

This will submit a job to the freia job queue that will ingest all of the shots in the tiny campaign and push them to the s3 bucket.





