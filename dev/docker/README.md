# Docker Files

This folder contains docker files for running the API in both development and production mode.

 - `docker-compose.yml` - this is the main docker compose file which configures different services.
 - `docker-compose-dev.yml` - this is an additional docker compose file which sets up development instance of the web server that automatically reloads changes in the local directory.
 - `Dockerfile` - this is the docker file for building the environment that the API will run in.
- `.env` - an environment configuration file which sets the admin user names and passwords for each service. This must be changed for a production system.

In order to test the nginx configuration the following steps must be taken:

Comment out everything associated with `certbot` docker container in the docker-compose-prod file.

Also in this compose file comment out the following lines in the nginx services volumes section:

```
./certbot/www:/var/www/certbot/:ro
./certbot/conf/:/etc/nginx/ssl/:ro
```

And uncomment out the following lines (Should be just below the previous two):

```
./self_cert.crt:/etc/ssl/certs/self_cert.crt:ro
./self_signed.key:/etc/ssl/private/self_signed.key:ro
```

Ensure where you are testing is port forwarding http and https ports (80,443) from you local router to your testing enviroment
In the nginx.conf file replace mastapp.site with your local IP
Also in the nginx.conf file in the https server section comment out the following lines:

```
ssl_certificate /etc/letsencrypt/live/mastapp.site/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/mastapp.site/privkey.pem;
```
And uncomment out the folowing lines (Should be just below the previous two):

```
ssl_certificate /etc/ssl/certs/self_cert.crt;
ssl_certificate_key /etc/ssl/private/self_signed.key;
```

Ensure openssl is installed in your testing enviroment
From the main directory (I.e. in fair-mast) Run the command: 

```
(sudo) openssl req -x509 -nodes -newkey rsa:2048 -keyout ./dev/docker/self_signed.key -out ./dev/docker/self_cert.crt
```

When running this command simply press enter to enter nothing when asked to add information (I.e. country code etc) DO NOT enter "." as stated in the help text

Now you can run the full project as described in the main README (I.e. running the full docker-compose with both compose files) and the api should be available on both localhost:8081 and on {IP}/
