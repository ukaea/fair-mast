[![License](https://img.shields.io/badge/license-MIT-blue)](https://opensource.org/license/MIT) [![Build Status](https://github.com/ukaea/fair-mast/actions/workflows/ci.yml/badge.svg)](https://github.com/ukaea/fair-mast/actions/workflows/ci.yml)

# FAIR MAST Data Management System

FAIR MAST is a data management system designed for fusion research, enabling efficient storage, retrieval, and management of experimental data.

## 📌 Development Setup

### Prerequisites	

- ### Mac Users

	If you are using Mac for development, use [podman](https://podman.io/docs/installation) instead of docker. Follow the installation guide to set it up, then follow the below set up. Also install ``podman-mac-helper``, which provides a compatibility layer that allows you to use most Docker commands with Podman on macOS.

	### Linux/Windows Users

	If using Linux or Windows, you need to make sure you have [docker](https://www.docker.com/get-started/) and `docker-compose` installed on your system.

### Getting Started

1. **Clone the repository:**

```bash
git clone git@github.com:ukaea/fair-mast.git
cd fair-mast
```

2. **Start the development environment:**

	- #### Mac Users

	```bash
	podman compose \
	--env-file dev/docker/.env.dev  \
	-f dev/docker/docker-compose.yml \
	up \
	--build
	```

	- #### Linux/Windows Users

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

3. **Shutting Down:**

	- #### Mac Users

	```bash
	podman compose -f dev/docker/docker-compose.yml down   
	podman volume rm --all
	```

	- #### Linux/Windows Users

	```bash
	docker-compose -f dev/docker/docker-compose.yml down
	```

### 📦 Populating the Database

Retrieve and ingest the metadata files using [s5cmd](https://github.com/peak/s5cmd):

```
s5cmd --no-sign-request --endpoint-url https://s3.echo.stfc.ac.uk cp "s3://mast/dev/mock_data*" ./tests
```

Create the database and ingest data using the following command:

- #### Mac Users

```bash
podman exec -it mast-api python -m src.api.create /code/data/index
```

- #### Linux/Windows Users

```bash
docker exec -it mast-api python -m src.api.create /code/data/index
```
### 🔓 Create .env File from .env.example
To configure Keycloak secrets for local development, follow these steps:
- 1. **Create a .env file** by copying the example template:
```bash
cp dev/docker/.env.example dev/docker/.env
```
- 2. Open dev/docker/.env and replace the placeholder values with the actual credentials retrieved from pwdstore.
- 3. Save the file. This .env file will be used to load your local secrets during development.

### ✅ Running Unit Tests

Verify everything is setup correctly by running the unit tests.

Follow the below instructions to set up the environment.

```bash
uv run pytest
```

## 🔧 Production Deployment

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

**⚠ Note:** Every time you destory volumes, the production server will mint a new certificate for HTTPS. Lets Encrypt currently limits this to [5 per week](https://letsencrypt.org/docs/duplicate-certificate-limit/).

You'll need to download and ingest the production data like so:

```bash
mkdir -p data/mast/meta
rsync -vaP <CSD3-USERNAME>@login.hpc.cam.ac.uk:/rds/project/rds-sPGbyCAPsJI/archive/metadata data/
```

```bash
docker exec -it mast-api python -m src.api.create /code/data/index
```

For information on testing the Nginx configuration in a testing enviroment see the README in /dev/docker.

## Building Documentation

See the [documentation guide](./docs/README.md) for more details.


## Citation

If you would like to reference this work, please cite the followig publication.

***Samuel Jackson, Saiful Khan, Nathan Cummings, James Hodson, Shaun de Witt, Stanislas Pamela, Rob Akers, Jeyan Thiyagalingam***, _FAIR-MAST: A fusion device data management system_, SoftwareX, Volume 27, 2024,101869,ISSN 2352-7110, [https://doi.org/10.1016/j.softx.2024.101869](https://doi.org/10.1016/j.softx.2024.101869).

In BibTex format:
```
@article{jackson_fair-mast_2024,
	title = {{FAIR}-{MAST}: {A} fusion device data management system},
	volume = {27},
	issn = {23527110},
	shorttitle = {{FAIR}-{MAST}},
	url = {https://linkinghub.elsevier.com/retrieve/pii/S2352711024002395},
	doi = {10.1016/j.softx.2024.101869},
	language = {en},
	urldate = {2025-01-17},
	journal = {SoftwareX},
	author = {Jackson, Samuel and Khan, Saiful and Cummings, Nathan and Hodson, James and De Witt, Shaun and Pamela, Stanislas and Akers, Rob and Thiyagalingam, Jeyan},
	month = sep,
	year = {2024},
	pages = {101869},
}
```
