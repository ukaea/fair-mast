from pathlib import Path
import pytest
pyuda_import = pytest.importorskip("pyuda") 
from src.archive.main import _do_write_signal, DatasetReader, DatasetWriter, read_config, get_file_system # noqa: E402

def test_write_diagnostic_signal(benchmark):
    source = 'AMC'
    output_path = f's3://mast/{source}'
    fs_config = Path('~/.s3cfg').expanduser()
    config = read_config(fs_config)
    fs = get_file_system(config)

    reader = DatasetReader()
    writer = DatasetWriter(output_path, fs=fs)

    metadata = {
        'shot': 30420,
        'dataset_item_uuid': 'abc',
        'status': 0
    }
    name = 'AMC_PLASMA CURRENT'

    result = _do_write_signal(metadata, name, reader, writer, True)
    assert isinstance(result, dict)