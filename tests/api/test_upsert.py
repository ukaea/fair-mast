import os

import pandas as pd

from src.api.create import connect, upsert

host = os.environ.get("DATABASE_HOST", "localhost")
TEST_DB_NAME = "test_db"
SQLALCHEMY_DATABASE_TEST_URL = f"postgresql://root:root@{host}:5432/{TEST_DB_NAME}"

def test_upsert(client, override_get_db):

    query = """
        query {
            scenarios {
                name
            }
        }
    """

    upsert_data = pd.DataFrame([
        {"id": 1, "name": "Updated Scenario Name", "title": "Tokamak Scenario"},  # Update existing row
        {"id": 35, "name": "New Scenario", "title": "New Tokamak Scenario"}       # Add new row
    ])
    metadata_obj, engine = connect(SQLALCHEMY_DATABASE_TEST_URL)
    upsert_data.to_sql("scenarios", con=engine, if_exists="append", index=False, method=upsert)

    updated_response = client.post("graphql", json={"query": query})
    assert updated_response.status_code == 200

    updated_data = updated_response.json()
    assert "errors" not in updated_data
    
    updated_data = pd.DataFrame(updated_data["data"]["scenarios"])
    names = updated_data['name'].tolist()

    assert len(updated_data) == 35
    assert "Updated Scenario Name" in names
    assert "New Scenario" in names