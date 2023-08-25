import os

host = os.environ.get("DATABASE_HOST", "localhost")

# Location of the database
SQLALCHEMY_DATABASE_URL = f"postgresql://root:root@{host}:5432/mast_db"
# Echo SQL statements
SQLALCHEMY_DEBUG = os.environ.get("SQLALCHEMY_DEBUG", False)
