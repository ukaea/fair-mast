# README

## Setup

Start the postgres and pg_admin by using docker compose

```bash
sudo docker compose up
```
Create the database and insert data:

```bash
python -m src.ingest
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