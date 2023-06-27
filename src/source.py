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
        result = []
        def _visitor(name, node):
            if name[0] !='x' and isinstance(node, h5py.Dataset):
                result.append(da.atleast_1d(da.from_array(node)))
        file_handle.visititems(_visitor)
        return result
            
    def read_signal_all_shots(self, name):
        signals = []
        for path in self.data_dir.glob('*.h5'):
            file_handle = h5py.File(path)
            if name in file_handle:
                data = da.atleast_1d(da.from_array(file_handle[name]))
                signals.append(data)
        signals = da.stack(signals, axis=0)
        return signals


class NetCDFSource:

    def __init__(self, path) -> None:
        self.path = Path(path)

    def read_signal_all_shots(self, name):
        data = xr.open_dataset(self.path / name) 
        return data[name.split('.')[0]]

    def read_shot_all_signals(self, shot):
       paths = list(self.path.glob('*.nc'))
       data = [xr.open_dataset(path) for path in paths]
       data = [data.sel(index=data.shot_id == int(shot)) for data in data]
       return data
        

class ZarrSource:

    def __init__(self, path) -> None:
        self.path = Path(path)

    def read_signal_all_shots(self, name):
        path = self.path / name
        data = xr.open_zarr(path)
        return data[name.split('.')[0]]

    def read_shot_all_signals(self, shot):
       paths = list(self.path.glob('*.zarr'))
       data = [xr.open_dataset(path) for path in paths]
       data = [data.sel(index=data.shot_id == int(shot)) for data in data]
       return data
