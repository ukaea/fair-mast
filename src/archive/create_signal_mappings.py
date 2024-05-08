import json
from pathlib import Path
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


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

    df = pd.read_parquet("data/uda/signals", schema=schema)
    df = df[["name", "uda_name"]].drop_duplicates()
    df = df.reset_index(drop=True)

    name_pairs = df.to_dict(orient="index")
    mapping = {}
    for item in name_pairs.values():
        new_name = item["name"]
        old_name = item["uda_name"]
        mapping[new_name] = {
            "MAP_TYPE": "PLUGIN",
            "PLUGIN": "UDA",
            "ARGS": {"signal": old_name},
        }

    file_name = "mappings/signals.json"
    with Path(file_name).open("w") as f:
        json.dump(mapping, f, indent=4)

    print(f"Wrote {file_name}")


if __name__ == "__main__":
    main()
