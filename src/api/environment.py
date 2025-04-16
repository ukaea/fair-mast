import os

from dotenv import load_dotenv

host = os.environ.get("DATABASE_HOST", "localhost")
keycloak_host = os.environ.get("KEYCLOAK_HOST", "localhost")
pg_user = os.environ.get("POSTGRES_USER")
pg_password = os.environ.get("POSTGRES_PASSWORD")

# Location of the database
DB_NAME = "mast_db"
SQLALCHEMY_DATABASE_URL = f"postgresql://{pg_user}:{pg_password}@{host}:5432/{DB_NAME}"
# Echo SQL statements
SQLALCHEMY_DEBUG = os.environ.get("SQLALCHEMY_DEBUG", False)

# Realm name within keycloak
REALM_NAME = "realm1"
# Client name withing keycloak
CLIENT_NAME = "fair-mast"

TEST_PASSWORD = "test"

UNAUTHORIZED_KEYCLOAK_USER = "test1"

# Keycloak server url
KEYCLOACK_SERVER_URL = f"http://{keycloak_host}:8080"

# Load keycloak secrets
load_dotenv("dev/docker/.env")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET")
KEYCLOAK_USERNAME = os.getenv("KEYCLOAK_USERNAME")
KEYCLOAK_PASSWORD = os.getenv("KEYCLOAK_PASSWORD")
