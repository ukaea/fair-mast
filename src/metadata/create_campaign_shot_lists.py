"""Get a list of shots for each campaign.
"""
from pathlib import Path
import requests
import pandas as pd


def build_query(campaign):
    query = f"""
        query {{
            all_shots (where: {{campaign: {{eq: "{campaign}"}}}}){{
                shots {{
                    shot_id
                }}
            }}
        }}
    """
    return query


def main():
    path = Path("campaign_shots")
    path.mkdir(exist_ok=True)
    graphql_api = "http://localhost:5000/graphql"

    for i in range(5, 10):
        campaign = f"M{i}"
        query = build_query(campaign)
        response = requests.post(f"{graphql_api}", json={"query": query})
        result = response.json()
        result = pd.DataFrame(result["data"]["all_shots"]["shots"])
        result.to_csv(path / f"{campaign}.csv", index=False)


if __name__ == "__main__":
    main()
