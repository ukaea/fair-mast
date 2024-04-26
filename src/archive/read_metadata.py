from asyncio import as_completed
import logging
import zarr
import s3fs
import pandas as pd
import argparse
from pathlib import Path
from dask_mpi import initialize
from dask.distributed import Client, as_completed
from src.archive.utils import read_shot_file


class SignalMetaDataParser:

    def __init__(self, bucket_path: str, output_path: str, fs: s3fs.S3FileSystem):
        self.bucket_path = bucket_path
        self.output_path = Path(output_path)
        self.fs = fs

    def __call__(self, shot: int):
        path = f"{self.bucket_path}/{shot}.zarr"
        store = zarr.storage.FSStore(path, fs=self.fs)

        items = []
        if not self.fs.exists(path):
            return shot

        with zarr.open_consolidated(store) as f:
            for source in f.keys():
                if f[source].attrs.get("type", "") == "Image":
                    metadata = f[source].attrs
                    metadata = dict(metadata)
                    metadata["group"] = f"{source}"
                    metadata["shape"] = f[source]["data"].shape
                    metadata["rank"] = sum(metadata["shape"])
                    items.append(metadata)
                else:
                    for key in f[source].keys():
                        metadata = f[source][key].attrs
                        metadata = dict(metadata)
                        metadata["group"] = f"{source}/{key}"
                        try:
                            metadata["shape"] = f[source][key]["data"].shape
                            metadata["rank"] = len(metadata["shape"])
                        except:
                            # Special case: if group name written with a "/" as the first character
                            # the structure is slightly different!
                            metadata["shape"] = f[source][key].shape
                            metadata["rank"] = len(metadata["shape"])
                        items.append(metadata)

        df = pd.DataFrame(items)
        df.to_parquet(self.output_path / f"{shot}.parquet")
        return shot


def main():
    initialize()
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        prog="UDA Archive Parser",
        description="Parse the MAST archive and writer to Zarr files. Upload to S3",
    )

    parser.add_argument("shot_file")
    parser.add_argument("bucket_path")
    parser.add_argument("output_path")

    args = parser.parse_args()

    client = Client()
    endpoint_url = f"https://s3.echo.stfc.ac.uk"
    fs = s3fs.S3FileSystem(anon=True, endpoint_url=endpoint_url)

    shot_list = read_shot_file(args.shot_file)

    path = Path(args.output_path) / "signals"
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
