import pandas as pd
import argparse
from pathlib import Path
import pyarrow as pa

schema = pa.schema(
    [
        ("uda_name", pa.string()),
        ("uuid", pa.string()),
        ("shot_id", pa.uint32()),
        ("name", pa.string()),
        ("description", pa.string()),
        ("version", pa.int64()),
        ("quality", pa.string()),
        ("signal_type", pa.string()),
        ("mds_name", pa.string()),
        ("format", pa.string()),
        ("source", pa.string()),
        ("file_name", pa.string()),
        ("dimensions", pa.list_(pa.string())),
        ("shape", pa.list_(pa.uint32())),
        ("rank", pa.uint32()),
    ]
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir")
    parser.add_argument("output_file")
    args = parser.parse_args()

    df = pd.read_parquet(args.source_dir, schema=schema)
    df.to_parquet(args.output_file, schema=schema)


if __name__ == "__main__":
    main()
