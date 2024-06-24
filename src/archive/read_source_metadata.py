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

logging.basicConfig(level=logging.INFO)


class SourceMetaDataParser:

    def __init__(self, bucket_path: str, output_path: str, fs: s3fs.S3FileSystem):
        self.bucket_path = bucket_path
        self.output_path = Path(output_path)
        self.fs = fs

    def __call__(self, source_file: Path):
        shot = source_file.stem
        path = f"{self.bucket_path}/{shot}.zarr"

        source_df = self.read_source_file(source_file)
        if source_df is None:
            return shot

        df = self.read_sources(path, source_df)

        if df is not None:
            df.to_parquet(self.output_path / f"{shot}.parquet")

        logging.info(f"Done {shot}")
        return shot

    def read_source_file(self, source_file: str) -> Optional[pd.DataFrame]:
        if not Path(source_file).exists():
            return None
        return pd.read_parquet(source_file)

    def read_source(self, path: str) -> Optional[pd.DataFrame]:
        try:
            store = zarr.storage.FSStore(path, fs=self.fs)
            with zarr.open_consolidated(store) as f:
                metadata = dict(f.attrs)
        except Exception:
            return None

        return metadata

    def read_sources(
        self, path: str, source_df: pd.DataFrame
    ) -> Optional[pd.DataFrame]:
        metadata_items = []
        for _, source in source_df.iterrows():
            source_name = source["name"]
            file_path = path + f"/{source_name}"
            metadata = source.to_dict()
            metadata["url"] = file_path
            source_metadata = self.read_source(file_path)
            if source_metadata is not None:
                metadata.update(source_metadata)
                metadata_items.append(metadata)

        if len(metadata_items) == 0:
            return None

        df = pd.DataFrame(metadata_items)
        return df


def main():
    logging.basicConfig(level=logging.INFO)
    initialize()

    parser = argparse.ArgumentParser(
        prog="UDA Archive Parser",
        description="Parse the MAST archive and writer to Zarr files. Upload to S3",
    )

    parser.add_argument("source_path")
    parser.add_argument("bucket_path")
    parser.add_argument("output_path")
    parser.add_argument("--endpoint_url", default="https://s3.echo.stfc.ac.uk")

    args = parser.parse_args()

    client = Client()
    fs = s3fs.S3FileSystem(anon=True, endpoint_url=args.endpoint_url)

    source_files = list(sorted(Path(args.source_path).glob("*.parquet")))

    path = Path(args.output_path)
    path.mkdir(exist_ok=True, parents=True)
    parser = SourceMetaDataParser(args.bucket_path, path, fs)

    tasks = []
    for source_file in source_files:
        task = client.submit(parser, source_file)
        tasks.append(task)

    n = len(tasks)
    for i, task in enumerate(as_completed(tasks)):
        shot = task.result()
        logging.info(f"Finished shot {shot} - {i+1}/{n} - {(i+1)/n*100:.2f}%")


if __name__ == "__main__":
    main()
