import pandas as pd
import zarr
import xarray as xr
import subprocess
from src.archive.uploader import UploadConfig
from pathlib import Path
import os
import pytest

pyuda_import = pytest.importorskip("pyuda")
from src.archive.writer import DatasetWriter  # noqa: E402
from src.archive.task import (
    CreateDatasetTask,
    CleanupDatasetTask,
    UploadDatasetTask,
    CreateSourceMetadataTask,
    CreateSignalMetadataTask,
)  # noqa: E402


def test_create_dataset_task(tmpdir, mocker):
    metadata_dir = tmpdir / "uda"
    shot = 30420
    task = CreateSignalMetadataTask(data_dir=metadata_dir / "signals", shot=shot)
    task()

    task = CreateSourceMetadataTask(data_dir=metadata_dir / "sources", shot=shot)
    task()

    task = CreateDatasetTask(metadata_dir, tmpdir, shot)

    mock_method = mocker.patch.object(task, "read_signal_info")
    mock_method.return_value = pd.read_parquet(
        metadata_dir / f"signals/{shot}.parquet"
    ).iloc[:3]

    task()

    dataset_path = tmpdir / f"{shot}.zarr"
    assert dataset_path.exists()

    handle = zarr.open_consolidated(dataset_path)
    source = handle["abm"]
    print(handle.tree())

    assert len(list(source.keys())) == 3
    ds = xr.open_zarr(dataset_path, group=f"abm")
    assert len(ds.data_vars) == 3


@pytest.mark.usefixtures("fake_dataset")
def test_write_cleanup(tmpdir, fake_dataset):
    shot = 30420
    writer = DatasetWriter(shot, tmpdir)
    writer.write_dataset(fake_dataset)

    assert writer.dataset_path.exists()
    task = CleanupDatasetTask(writer.dataset_path)
    task()
    assert not writer.dataset_path.exists()


def test_upload_dataset(mocker):
    mocker.patch("subprocess.run")

    config = UploadConfig(
        credentials_file=".s5cfg.stfc",
        endpoint_url="https://s3.echo.stfc.ac.uk",
        url="s3://mast/test/",
    )

    local_file = "30420.zarr"

    env = os.environ.copy()
    uploader = UploadDatasetTask(local_file, config)
    uploader()

    subprocess.run.assert_called_once_with(
        [
            "s5cmd",
            "--credentials-file",
            config.credentials_file,
            "--endpoint-url",
            config.endpoint_url,
            "cp",
            "--acl",
            "public-read",
            local_file,
            config.url,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        env=env,
    )


def test_source_metadata_reader(tmpdir):
    shot = 30420
    task = CreateSourceMetadataTask(data_dir=tmpdir, shot=shot)
    task()

    path = Path(tmpdir / f"{shot}.parquet")
    assert path.exists()
    df = pd.read_parquet(path)
    assert isinstance(df, pd.DataFrame)


def test_signal_metadata_reader(tmpdir):
    shot = 30420
    task = CreateSignalMetadataTask(data_dir=tmpdir, shot=shot)
    task()

    path = Path(tmpdir / f"{shot}.parquet")
    assert path.exists()
    df = pd.read_parquet(path)
    assert isinstance(df, pd.DataFrame)
