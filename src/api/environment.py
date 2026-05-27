import os

host = os.environ.get("DATABASE_HOST", "localhost")
pg_user = os.environ.get("POSTGRES_USER")
pg_password = os.environ.get("POSTGRES_PASSWORD")

# Location of the database
DB_NAME = "mast_db"
SQLALCHEMY_DATABASE_URL = f"postgresql://{pg_user}:{pg_password}@{host}:5432/{DB_NAME}"
# Echo SQL statements
SQLALCHEMY_DEBUG = os.environ.get("SQLALCHEMY_DEBUG", False)

SITE_URL = "http://localhost:8081"
if "VIRTUAL_HOST" in os.environ:
    SITE_URL = f"https://{os.environ.get('VIRTUAL_HOST')}"

#data license
LICENSE_URL = os.environ.get(
    "LICENSE_URL",
    "https://creativecommons.org/licenses/by-sa/4.0/",
)