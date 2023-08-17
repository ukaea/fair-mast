# README
# FAIR MAST Archive

## Development

Run the develop container to start the postgres database and fastapi containers locally. The development environment will watch the source directory and automatically reload changes.

```bash
docker-compose -f docker-compose.yml -f docker-compose-dev.yml up --build
```

To create the database and populate it with content we need to get the metadata files. These are currently stored on CSD3. You can sync them to your local repo with the following rsync command:

```bash
rsync -vaP ir-jack5@login.hpc.cam.ac.uk:/rds/project/rds-sPGbyCAPsJI/archive/meta data/
/rds/rds-ukaea-mast-sPGbyCAPsJI/archive/meta
```

Assuming that the meta data files have been copied to a folder called `./data/meta` in the local directory, we can 
create the database and ingest data using the following command:

```bash
docker exec -it mast-api python -m src.api.create /code/data/meta
```

### Running Tests
To run the unit tests you may use `pytest` like so:

```bash
python -m pytest tests
```