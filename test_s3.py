import s3fs
import zarr
import numpy as np

file_name = 'amc_test.zarr'

s3 = s3fs.S3FileSystem(
    anon=True,
    use_ssl=False,
    client_kwargs={
        "endpoint_url": "http://localhost:9000"
    },
)

store = zarr.storage.FSStore(f'mast/{file_name}', fs=s3, exceptions=())
handle = zarr.open_consolidated(store)
arr = handle['28415']['data'][:]
assert not np.all(arr == 0)

g = handle['28412']
data = g['data']
arr = data[:]
assert not np.all(arr == 0)