import os

host = os.environ.get("DATABASE_HOST", "localhost")

# Location of the database
DB_NAME = "mast_db"
SQLALCHEMY_DATABASE_URL = f"postgresql://root:root@{host}:5432/{DB_NAME}"
# Echo SQL statements
SQLALCHEMY_DEBUG = os.environ.get("SQLALCHEMY_DEBUG", False)
