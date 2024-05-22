import json
from pathlib import Path
from numpy import source
import pandas as pd
import pyarrow as pa


def main():
    schema = pa.schema(
        [
            ("uda_name", pa.string()),
            ("uuid", pa.string()),
            ("shot_id", pa.uint64()),
            ("name", pa.string()),
            ("version", pa.int64()),
            ("quality", pa.string()),
            ("signal_type", pa.string()),
            ("mds_name", pa.string()),
            ("format", pa.string()),
            ("source", pa.string()),
            ("file_name", pa.string()),
        ]
    )

    df = pd.read_parquet(
        "data/uda/signals", schema=schema, columns=["name", "uda_name", "source"]
    )
    df = df.drop_duplicates()
    df = df.reset_index(drop=True)
    print("Loaded signals")

    source_df = pd.read_parquet(
        "data/uda/sources",
        schema=schema,
        columns=["name", "format", "signal_type"],
    )
    source_df = source_df.drop_duplicates()
    source_df = source_df.reset_index(drop=True)
    source_df = source_df.rename(dict(name="source"), axis=1)
    print("Loaded sources")

    df = df.merge(source_df, left_on="source", right_on="source")

    name_pairs = df.to_dict(orient="index")
    mapping = {}
    for item in name_pairs.values():
        new_name = item["name"]
        old_name = item["uda_name"]
        mapping[new_name] = {
            "MAP_TYPE": "PLUGIN",
            "PLUGIN": "UDA",
            "ARGS": {
                "signal": old_name,
                "format": item["format"],
                "type": item["signal_type"],
            },
        }

    file_name = "mappings/signals.json"
    with Path(file_name).open("w") as f:
        json.dump(mapping, f, indent=4)

    print(f"Wrote {file_name}")


if __name__ == "__main__":
    main()
