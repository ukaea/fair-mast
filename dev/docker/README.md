# Docker Files

This folder contains docker files for running the API in both development and production mode.

 - `docker-compose.yml` - this is the main docker compose file which configures different services.
 - `docker-compose-dev.yml` - this is an additional docker compose file which sets up development instance of the web server that automatically reloads changes in the local directory.
 - `Dockerfile` - this is the docker file for building the environment that the API will run in.
- `.env` - an environment configuration file which sets the admin user names and passwords for each service. This must be changed for a production system.