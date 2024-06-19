import pytest
import numpy as np
import xarray as xr


@pytest.fixture
def fake_dataset():
    return xr.Dataset(
        data_vars=dict(
            data=("time", np.random.random(10)),
            time=("time", np.random.random(10)),
            error=("time", np.random.random(10)),
        ),
        attrs={"name": "amc/plasma_current", "shot_id": 30420},
    )


@pytest.fixture
def fake_image():
    return xr.Dataset(
        data_vars=dict(
            data=(("frames", "heigth", "width"), np.random.random((20, 10, 10))),
        ),
        attrs={"name": "rbb", "shot_id": 30420},
    )


@pytest.fixture
def fake_channel_dataset(fake_dataset):
    channels = {f"channel{i}": fake_dataset["data"] for i in range(10)}
    for channel in channels.values():
        channel.attrs.update(fake_dataset.attrs)
    return xr.Dataset(channels)
