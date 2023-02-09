import h5py
import dask
import numpy as np
import dask.array as da
import dask.bag as db
from pathlib import Path
import xarray as xr

class HDFSource:
    
    def __init__(self, data_dir) -> None:
        self.data_dir = Path(data_dir)

    def read_shot_all_signals(self, shot):
        path = self.data_dir  / f'{shot}.h5'
        file_handle = h5py.File(path)
        result = {}
        def _visitor(name, node):
            if isinstance(node, h5py.Dataset):
                result[name] = da.atleast_1d(da.from_array(node))
        file_handle.visititems(_visitor)
        return result
            
    def read_signal_all_shots(self, name):
        signals = []
        for path in self.data_dir.glob('*.h5'):
            result = self._read_signal(path, name)
            signals.append(result)
        signals = da.stack(signals, axis=0)
        return signals

    def _read_signal(self, path, name):
        file_handle = h5py.File(path)
        data = da.atleast_1d(da.from_array(file_handle[name]))
        return data

class NetCDFSource:

    def __init__(self, path) -> None:
        self.path = Path(path)

    def read_signal_all_shots(self, name):
        return xr.open_dataset(self.path / name) 

class ZarrSource:

    def __init__(self, path) -> None:
        self.path = Path(path)

    def read_signal_all_shots(self, name):
        path = self.path / name
        return xr.open_zarr(path) 