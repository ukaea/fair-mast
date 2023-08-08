Tools for creating the metadata

## Setup

Start the postgres and pg_admin by using docker compose

```bash
sudo docker compose up
```

Mount the remote data archive, including the metadata files:

```bash
mkdir ~/mast-data
sshfs -o allow_other,auto_cache,reconnect  ~/mast-data ir-jack5@login-cpu.hpc.cam.ac.uk:/home/ir-jack5/rds/rds-ukaea-mast-sPGbyCAPsJI/archive
```

Create the database and insert data:

```bash
python -m src.ingest ~/mast-data/meta
```

## Accessing the Container

To access the postgres shell we can ssh into the running container:

```bash
sudo docker exec -it pg_container /bin/bash
```

By default the code is mounted folder in the `/app` folder.

```bash
cd /app
```