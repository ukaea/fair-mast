# Docker Files

This folder contains docker files for running the API in both development and production mode.

 - `docker-compose.yml` - this is the main docker compose file which configures different services.
 - `docker-compose-dev.yml` - this is an additional docker compose file which sets up development instance of the web server that automatically reloads changes in the local directory.
 - `Dockerfile` - this is the docker file for building the environment that the API will run in.
- `.env` - an environment configuration file which sets the admin user names and passwords for each service. This must be changed for a production system.

In order to test the nginx configuration the following steps must be taken:

In the .env.dev file containing the enviromental variables used by the containers, switch which of the nginx and certbot varibles are commented out, such that the top option is active.
These are:
NGINX_CONFIG_PATH, to switch to the testing nginx cofig file
CERTBOT_COMMAND, to switch which command certbot runs upon start-up
NOTE: Certbot will only work if the testing enviroment is associated with a registered domain (I.e. mastapp.site)

Ensure openssl is installed in your testing enviroment
From the main directory (I.e. in fair-mast) Run the command: 

```bash
(sudo) openssl req -x509 -nodes -newkey rsa:2048 -keyout ./dev/docker/certbot/conf/live/self_signed/privkey.pem -out ./dev/docker/certbot/conf/live/self_signed/fullchain.pem -subj "/C=/ST=/L=/O=/OU=/CN="
```

Now you can run the full project as described in the main README (I.e. running the full docker-compose with both compose files) and the api should be available on https:127.0.0.1/
NOTE: When connecting to this most browsers will warn you that it is not secure, this is due to the use of self-signed certificates (These are only used for testing, not in production). To continue to the doccumentation simply click "Advanced" and "Proceed anyway" or similar options.
