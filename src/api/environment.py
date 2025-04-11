import os

host = os.environ.get("DATABASE_HOST", "localhost")
pg_user = os.environ.get("POSTGRES_USER")
pg_password = os.environ.get("POSTGRES_PASSWORD")

# Location of the database
DB_NAME = "mast_db"
SQLALCHEMY_DATABASE_URL = f"postgresql://{pg_user}:{pg_password}@{host}:5432/{DB_NAME}"
# Echo SQL statements
SQLALCHEMY_DEBUG = os.environ.get("SQLALCHEMY_DEBUG", False)
