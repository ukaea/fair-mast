from pathlib import Path
import yaml
import zarr
from rich.progress import Progress

def main():
    catalog_data = {
        'description': 'The MAST Data Archive Catalog',
        'metadata': dict(version=1),
        'sources': {}
    }

    paths = Path('data/mast').glob('*.zarr')
    paths = list(sorted(paths))

    with Progress() as progress:
        task = progress.add_task("Compiling Catalog", total=len(paths))
        for path in paths:
            progress.console.print(path)
            store = zarr.open(path, mode='r')
            _, item = next(store.groups())
            metadata = dict(item.attrs)
            name = path.stem

            source = {
                'description': metadata['label'],
                'driver': 'zarr',
                'metadata': metadata,
                'args': {
                    'urlpath': '{{ CATALOG_DIR }}' + path.name
                }
            }
            catalog_data['sources'][name] = source
            progress.advance(task)

    catalog_file = Path('data/mast/catalog.yml')
    with catalog_file.open('w') as handle:
        yaml.safe_dump(catalog_data, handle)


if __name__ == "__main__":
    main()