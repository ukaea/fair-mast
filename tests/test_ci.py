def test_query_shots(client, override_get_db):
    query = """
        query {
            all_shots (limit: 10) {
                shots {
                    shot_id
                }
                page_meta {
                    next_cursor
                    total_items
                }
            }
        }
    """
    response = client.post("graphql", json={"query": query})
    assert response.status_code == 200

    data = response.json()
    assert "errors" not in data