import pytest
import numpy as np
import xarray as xr

@pytest.fixture
def fake_dataset():
    return xr.Dataset(
        data_vars=dict(
            data=np.random.random(10),
            time=np.random.random(10),
            error=np.random.random(10),
        ),
        attrs={"name": "ACM_FAKE_DATASET"},
    )
