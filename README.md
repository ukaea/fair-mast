# README

## Setup

Start the postgres and pg_admin by using docker compose

```bash
sudo docker compose up
```

To access the postgres shell we need to ssh into the running container:

```bash
sudo docker exec -it pg_container /bin/bash
```

Then you can access the `pgsql` as follows:

```bash
psql -d mast_db
```