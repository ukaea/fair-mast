from typing import Optional, Union
import datasets
import xarray as xr
import zarr

from datasets.splits import Split, SplitDict, SplitGenerator, SplitInfo

__version__ = '1.0.0'

_BASE_URL = "zip://::hf://datasets/sljack/mast/"

class MastFusionDataConfig(datasets.BuilderConfig):
 
    def __init__(self, shot_ids=None, return_xarray=False, **kwargs):
        super(MastFusionDataConfig, self).__init__(version=datasets.Version(__version__), **kwargs)
        self.shot_ids = shot_ids
        self.return_xarray = return_xarray

ALL_FEATURES = {
    "AMC_PLASMA_CURRENT": datasets.Features({
        'data': datasets.Sequence(datasets.Value('float32')),
        'error': datasets.Sequence(datasets.Value('float32')),
        'Time (sec)': datasets.Sequence(datasets.Value('float32')),
    }),
    "EFM_PSI_R_Z": datasets.Features({
        'data': datasets.Array3D(shape=(None, 65, 65), dtype='float32'),
        'error': datasets.Array3D(shape=(None, 65, 65), dtype='float32'),
        'Time': datasets.Sequence(datasets.Value('float32')),
        'Height': datasets.Sequence(datasets.Value('float32')),
        'Radius': datasets.Sequence(datasets.Value('float32')),
    })
}

class MastFusionData(datasets.GeneratorBasedBuilder):

    BUILDER_CONFIGS = [
        MastFusionDataConfig(name="AMC_PLASMA_CURRENT", description="Plasma Current Data", shot_ids=None),
        MastFusionDataConfig(name="EFM_PSI_R_Z", description="Equillibrium Reconstruction", shot_ids=None)
    ]

    BUILDER_CONFIG_CLASS = MastFusionDataConfig

    def _info(self):
         return datasets.DatasetInfo(
            description='MAST Fusion Data',
            supervised_keys=None,
            features=ALL_FEATURES[self.config.name]
        )

    def _split_generators(self, dl_manager):
        name = self.config.name
        url = f'data/{name}.zarr.zip'
        archive_path = dl_manager.download_and_extract(url)
        streaming = dl_manager.is_streaming

        return [
            datasets.SplitGenerator(
                name="full",
                gen_kwargs={
                    "path": url if streaming else archive_path,
                    "streaming": streaming,
                },
            ),
        ]

    def _generate_examples(self, path, streaming=False):
        if streaming:
            path = _BASE_URL+path
            store = zarr.storage.FSStore(url=path, mode='r', dimension_separator='/')
            keys = [key.split('/')[0] for key in store.keys() if not key.startswith('.')]
            keys = set(keys)
        else:
            store = zarr.open(path, mode='r')
            keys = list(store.keys())

        shot_ids = self.config.shot_ids

        if not streaming and self.config.return_xarray:
            raise NotImplementedError("Returning an xarray object when streaming=False is not currently supported!")

        for key in keys:
            if shot_ids is None or key in shot_ids:
                data = xr.open_zarr(path, group=key, chunks={})
                if streaming and self.config.return_xarray:
                    yield key, data
                else:
                    item = {k: v.values for k, v in data.data_vars.items()}
                    item.update({k: v.values for k, v in data.coords.items()})
                    yield key, item

                    