import pandas as pd
import logging
from rich.progress import track
from src.uda import UDAClient


def get_source_info(client: UDAClient, shot: int):
    sources = client.list_sources(shot)
    if sources is None:
        return []

    items = []
    for source in sources:
        item = {}
        item['pass'] = source.pass_
        item['source_alias'] = source.source_alias
        item['description'] = source.description
        item['format'] = source.format
        item['filename'] = source.filename
        item['type'] = source.type
        item['status'] = source.status
        item['shot'] = source.shot
        items.append(item)

    return items

def main():
    logger = logging.getLogger("sources_log")
    logger.setLevel("INFO")

    shots = pd.read_csv('campaign.csv', index_col=None)['shot_id'].values
    shots = list(sorted(shots))

    client = UDAClient(logger)
    sources = []
    for shot in track(shots):
        items = get_source_info(client, shot)
        sources.extend(items)

    sources_df = pd.DataFrame(sources)
    sources_df.to_parquet('sources_metadata.parquet')



if __name__ == "__main__":
    main()
