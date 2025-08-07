# Docker Files

This folder contains docker files for running the API in both development and production mode.

 - `docker-compose.yml` - this is the main docker compose file which configures different services.
 - `docker-compose-network.yml` - this is an additional docker compose file which sets up nginx as a reverse proxy for networking, and certbot for the generation and renewal of ssl certificates
 - `Dockerfile` - this is the docker file for building the environment that the API will run in.
- `.env.dev` - an environment configuration file which sets the admin user names and passwords for each service and several config variables for nginx and certbot. This must be changed for a production system.

# SSL self certification

If you are just going to be using self signed certificates for local testing then here is how to generate the required self signed certiifcates:

Ensure openssl is installed in your enviroment
From the main directory (I.e. in fair-mast) Run the command: 

```bash
(sudo) openssl req -x509 -nodes -newkey rsa:2048 -keyout ./dev/docker/certbot/conf/live/self_signed/privkey.pem -out ./dev/docker/certbot/conf/live/self_signed/fullchain.pem -subj "/C=/ST=/L=/O=/OU=/CN="
```

Now you can run the full project as described in the main README (I.e. running the full docker compose with both compose files) and the api should be available on https:127.0.0.1/
NOTE: When connecting to this most browsers will warn you that it is not secure, this is due to the use of self-signed certificates (These are only used for testing, not in production). To continue to the documentation (If built, see the README in /docs or on the default page brought up when connecting to 127.0.0.1/) simply click "Advanced" and "Proceed anyway" or similar options.
