import pytest
import subprocess
import zarr
import xarray as xr
import subprocess
from pathlib import Path
from src.archive.uploader import UploadConfig
from src.archive.reader import DatasetReader
from src.archive.writer import DatasetWriter
from src.archive.task import CreateDatasetTask, CleanupDatasetTask, UploadDatasetTask


def test_do_task(tmpdir, mocker):
    mocker.patch("subprocess.run")

    config = UploadConfig(
        credentials_file=".s5cfg.stfc",
        endpoint_url="https://s3.echo.stfc.ac.uk",
        url="s3://mast/test/",
    )

    shot = 30420
    reader = DatasetReader(shot)
    signals = reader.list_datasets()
    signals = signals[:3]

    task = CreateDatasetTask(tmpdir, shot, config)

    mock_method = mocker.patch.object(task.reader, "list_datasets")
    mock_method.return_value = signals

    task()

    dataset_path = tmpdir / f"{shot}.zarr"
    assert dataset_path.exists()

    handle = zarr.open_consolidated(dataset_path)
    source = handle["abm"]

    assert len(list(source.keys())) == 3
    for name in source.keys():
        xr.open_zarr(dataset_path, group=f"abm/{name}")


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
    )
