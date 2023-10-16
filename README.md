# FAIR MAST Data Management System

## Overview


## Development Setup

### Pre-requisities

Before setting up you need to make sure you have [docker](https://www.docker.com/get-started/) and `docker-compose` installed on your system. You should also have a fresh `conda` or `venv` environment. We will assume you are using `conda`. First clone the repository:

```bash
git clone git@github.com:stfc-sciml/fair-mast.git
cd fair-mast
```

Then create a new environment and install the requirements:

```bash
conda create -n mast python=3.11
conda activate mast
pip install -r requirements.txt
```

### Start the Data Management System
Run the development container to start the postgres database, fastapi, and minio containers locally. The development environment will watch the source directory and automatically reload changes to the API as you work.

```bash
docker-compose -f dev/docker/docker-compose.yml -f dev/docker/docker-compose-dev.yml up --build
```

The following services will be started:

 - FastAPI REST & GraphQL Server - will start running at `http://localhost:5000`. 
    - The REST API documentation is at `http://localhost:5000/redoc`. 
    - The GraphQL API documentation is at `http://localhost:5000/graphql`.
 - Postgres Database Server - will start running at `http://localhost:5432`
 - Postgres Admin Server - will start running at `http://localhost:5050`
 - Minio S3 Storage Server - will start running at `http://localhost:9000`.
    - The admin web GUI will be running at `http://localhost:9001`. 

### Populate the Database
To create the database and populate it with content we need to get the metadata files. These are currently stored on CSD3. You can sync them to your local repo with the following rsync command:


```bash
mkdir -p data/mast/meta
rsync -vaP ir-jack5@login.hpc.cam.ac.uk:/rds/project/rds-sPGbyCAPsJI/archive/meta data/mast/meta
```

Assuming that the meta data files have been copied to a folder called `./data/mast/meta` in the local directory, we can 
create the database and ingest data using the following command:

```bash
docker exec -it mast-api python -m src.api.create /code/data/meta
```

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

### Running Unit Tests
To run the unit tests you may use `pytest` like so:

```bash
python -m pytest tests
```

This will run some unit tests for the REST and GraphQL APIs against the data in the database.
