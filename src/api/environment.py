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
REALM_NAME = "Culham"
# Client name withing keycloak
CLIENT_NAME = "Mastapp"

TEST_PASSWORD = "test"

UNAUTHORIZED_KEYCLOAK_USER = "test1"

# Keycloak server url
KEYCLOACK_SERVER_URL = "https://auth.ukaea.uk/auth/"

# Load keycloak secrets
load_dotenv(dotenv_path="dev/docker/.env", override=True)
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET")
KEYCLOAK_USERNAME = os.getenv("KEYCLOAK_USERNAME")
KEYCLOAK_PASSWORD = os.getenv("KEYCLOAK_PASSWORD")
AUTHORIZATION_CODE = os.getenv("KEYCLOAK_AUTHORIZED_CODE")
