[![License](https://img.shields.io/badge/license-MIT-blue)](https://opensource.org/license/MIT) [![Build Status](https://github.com/ukaea/fair-mast/actions/workflows/ci.yml/badge.svg)](https://github.com/ukaea/fair-mast/actions/workflows/ci.yml)

# FAIR MAST Data Management System

FAIR MAST is a data management system designed for fusion research, enabling efficient storage, retrieval, and management of experimental data.

[Look here](https://mastapp.site/) to find the public version of the FAIR MAST data catalog.

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
	docker compose --env-file dev/docker/.env.dev  -f dev/docker/docker-compose.yml up --remove-orphans --build --force-recreate -d 
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
	docker compose -f dev/docker/docker-compose.yml down --remove-orphans
	```

### 📦 Populating the Database

Retrieve and ingest the metadata files using [s5cmd](https://github.com/peak/s5cmd):

```
s5cmd --no-sign-request --endpoint-url https://s3.echo.stfc.ac.uk cp "s3://mast/dev/mock_data*" ./tests
```

Create the database and ingest data using the following command:

- #### Mac Users

```bash
podman exec -it mast-api python -m src.api.create /test_data/index/  
```

- #### Linux/Windows Users

```bash
docker exec -it mast-api python -m src.api.create /test_data/index/  
```

### ✅ Running Unit Tests

Verify everything is setup correctly by running the unit tests.

Follow the below instructions to set up the environment.

```bash
uv run pytest
```
## Documentation Building

In order to build the documentation simply run the following command from the base folder:

```bash
uv run jb build docs --path-output docs/built_docs
```

Once it has finished running simply restart (or run for the first time) the docker containers using:

```bash
docker compose --env-file dev/docker/.env.dev  -f dev/docker/docker-compose.yml up --remove-orphans --build --force-recreate -d
```

Or equivalent



## 🔧 Networked Deployment

### First time deployment

When deploying for the first time (I.e. with no ssl certificates yet generated) you will need to follow some additional steps:

If you are simply using self signed certificates (I.e. for testing/development) then follow the steps in the README in /dev/docker to generate some and ensure NGINX_CONFIG_PATH is set to "./nginx-test.conf" in .env.dev.

Also ensure that the top option for CERTBOT_COMMAND in .env.dev is the option not commented out so that no real ssl certiifcation takes place.
(Note in this instance certbot will probably exit while doing basically nothing or returing an error as it isn't needed)

Otherwise if you are going to be generating and using real ssl certificates ensure that NGINX_CONFIG_PATH is set to ./nginx.conf and and follow the instructions below:

Rename the file "nginx.conf" to "nginx-final.conf" (or anything else so long as you remember what it is)
Then rename: "nginx-initial.conf" to "nginx.conf" 

(This is so that nginx can run without ssl certiifcates while they are being generated)

You will also need to ensure that the bottom varient of the CERTBOT_COMMAND is not commented out in .env.dev (And the top version is) while also changing any instance of mastapp.site within the command to the domain you are using.

Proceed with the full deployment proceedure (As detailed below)

When back from deployment procedure:
Now switch the nginx config files back to their original names and run the command:

```bash
docker exec reverse-proxy nginx -s reload
```

(This reloads nginx to use the full configuration now inculding https with the generated certificates)

### Deployment procedure

When deploying the full networked stack (Either for testing or production) please check the .env.dev file in ./dev/docker and ensure the enviromental variable NGINX_CONFIG_PATH is set to it's correct varients for your use case (As detailed above in first time deployment).

To run the full networked project which starts the following containers/services: postgres database, fastapi, nginx reverse proxy and certbot ssl certificate generator/renewer, run the following command:

```bash
docker-compose --env-file dev/docker/.env.dev  -f dev/docker/docker-compose.yml -f dev/docker/docker-compose-prod.yml up --build --force-recreate --remove-orphans -d
```
NOTE: Certbot will only work if the enviroment is associated with a registered domain (I.e. mastapp.site), if you are simply testing 

You'll then need to download and ingest the production data like so:

```bash
mkdir -p data/mast/meta
rsync -vaP <CSD3-USERNAME>@login.hpc.cam.ac.uk:/rds/project/rds-sPGbyCAPsJI/archive/metadata data/
```

```bash
docker exec -it mast-api python -m src.api.create /test_data/index
```

(Note if this is a first time deployment now you return to the above section and change the nginx config)

### Shutdown procedure

To shut down the production deployment, run the following command:

```bash
docker-compose --env-file dev/docker/.env.dev  -f dev/docker/docker-compose.yml -f dev/docker/docker-compose-prod.yml down
```

To also destory the volumes (including the metadatabase) you may add the volumes parameter:

```bash
docker-compose --env-file dev/docker/.env.dev  -f dev/docker/docker-compose.yml -f dev/docker/docker-compose-prod.yml down --volumes
```


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
