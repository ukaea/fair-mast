# FAIR MAST Data Management System

## Development Setup

### Start the Data Management System
Run the develop container to start the postgres database and fastapi containers locally. The development environment will watch the source directory and automatically reload changes to the API as you work.

```bash
docker-compose -f docker-compose.yml -f docker-compose-dev.yml up --build
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
rsync -vaP ir-jack5@login.hpc.cam.ac.uk:/rds/project/rds-sPGbyCAPsJI/archive/meta data/
```

Assuming that the meta data files have been copied to a folder called `./data/meta` in the local directory, we can 
create the database and ingest data using the following command:

```bash
docker exec -it mast-api python -m src.api.create /code/data/meta
```

### Uploading Data to the Minio Storage

First, follw the [instructions to install the minio client](https://min.io/docs/minio/linux/reference/minio-mc.html) tool.

Next, configure the endpoint location. The development minio installation runs at `localhost:9000` and has the following default username and password:

```
mc alias set srv http://localhost:9000 minio99 minio123;
```

Then you can copy data to the bucket using:

```
mc cp --recursive <path-to-data> srv/mast
```

### Running Unit Tests
To run the unit tests you may use `pytest` like so:

```bash
python -m pytest tests
```
