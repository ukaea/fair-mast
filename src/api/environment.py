import os

host = os.environ.get("DATABASE_HOST", "localhost")

# Location of the database
DB_NAME = "mast_db"
SQLALCHEMY_DATABASE_URL = f"postgresql://root:root@{host}:5432/{DB_NAME}"
# Echo SQL statements
SQLALCHEMY_DEBUG = os.environ.get("SQLALCHEMY_DEBUG", False)

# Keycloak server url
SERVER_URL = "http://keycloak:8080"
# Realm name within keycloak
REALM_NAME = "realm1"
# Client name withing keycloak
CLIENT_NAME = "fair-mast-test"
# Keycloak client secret key
CLIENT_SECRET = "wZNwMVNtWgTSwZAFqeDQIPm6JFea72lB"

TEST_USERNAME = "test"
TEST_PASSWORD = "test"

UNAUTHORIZED_USER = "test1"
