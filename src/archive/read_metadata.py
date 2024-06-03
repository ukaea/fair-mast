from curses import meta
import logging
from typing import Optional
import zarr
import zarr.storage
import s3fs
import pandas as pd
import argparse
from pathlib import Path
from dask_mpi import initialize
from dask.distributed import Client, as_completed
from src.archive.utils import read_shot_file
import pyarrow as pa

logging.basicConfig(level=logging.INFO)

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
        ("dimensions", pa.list_(pa.string())),
        ("shape", pa.list_(pa.uint64())),
        ("rank", pa.uint64()),
    ]
)


class SignalMetaDataParser:

    def __init__(self, bucket_path: str, output_path: str, fs: s3fs.S3FileSystem):
        self.bucket_path = bucket_path
        self.output_path = Path(output_path)
        self.fs = fs

    def __call__(self, shot: int):
        path = f"{self.bucket_path}/{shot}.zarr"

        if not self.fs.exists(path):
            return shot

        source_df = self.read_source_file(shot)
        if source_df is None:
            return shot

        df = self.read_sources(path, source_df)

        if df is not None:
            df.to_parquet(self.output_path / f"{shot}.parquet", schema=schema)

        return shot

    def read_source_file(self, shot: int) -> Optional[pd.DataFrame]:
        source_file = f"data/uda/sources/{shot}.parquet"
        if not Path(source_file).exists():
            return None
        return pd.read_parquet(source_file)

    def read_source(self, path: str) -> Optional[pd.DataFrame]:
        if not self.fs.exists(path):
            return None

        store = zarr.storage.FSStore(path, fs=self.fs)
        items = []
        with zarr.open_consolidated(store) as f:
            for key, value in f.items():
                metadata = dict(value.attrs)
                if "shot_id" not in metadata:
                    logging.warning(f"{path}/{key} does not have a shot id")
                    continue
                metadata["uda_name"] = metadata.get("uda_name", "")
                metadata["dimensions"] = value.attrs["_ARRAY_DIMENSIONS"]
                metadata["shape"] = list(value.shape)
                metadata["rank"] = len(metadata["shape"])
                items.append(metadata)

        if len(items) == 0:
            return None

        df = pd.DataFrame(items)
        return df

    def read_sources(
        self, path: str, source_df: pd.DataFrame
    ) -> Optional[pd.DataFrame]:
        metadata_items = []
        for _, source in source_df.iterrows():
            source_name = source["name"]
            file_path = path + f"/{source_name}"
            logging.info(f"Reading {file_path}")
            metadata = self.read_source(file_path)
            if metadata is not None:
                metadata_items.append(metadata)

        if len(metadata_items) == 0:
            return None

        df = pd.concat(metadata_items)
        return df


def main():
    initialize()

    parser = argparse.ArgumentParser(
        prog="UDA Archive Parser",
        description="Parse the MAST archive and writer to Zarr files. Upload to S3",
    )

    parser.add_argument("shot_file")
    parser.add_argument("bucket_path")
    parser.add_argument("output_path")
    parser.add_argument("--endpoint_url", default="https://s3.echo.stfc.ac.uk")

    args = parser.parse_args()

    client = Client()
    fs = s3fs.S3FileSystem(anon=True, endpoint_url=args.endpoint_url)

    shot_list = read_shot_file(args.shot_file)

    path = Path(args.output_path)
    path.mkdir(exist_ok=True, parents=True)
    parser = SignalMetaDataParser(args.bucket_path, path, fs)

    tasks = []
    for shot in shot_list:
        task = client.submit(parser, shot)
        tasks.append(task)

    n = len(tasks)
    for i, task in enumerate(as_completed(tasks)):
        shot = task.result()
        logging.info(f"Finished shot {shot} - {i+1}/{n} - {(i+1)/n*100:.2f}%")


if __name__ == "__main__":
    main()
