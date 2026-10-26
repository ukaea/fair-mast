# Metadata

Metadata for every shot, source and signal is published as Parquet files in the public S3 bucket. No credentials are needed.

| Access | Location |
|---|---|
| S3 | `s3://mast/fairmast-meta/`, endpoint `https://s3.echo.stfc.ac.uk` |
| HTTPS | `https://s3.echo.stfc.ac.uk/mast/fairmast-meta/` |

## Files

| File | Contents |
|---|---|
| `l1_shots.parquet`, `l2_shots.parquet` | One row per shot: shot metadata and CPF summary statistics |
| `l1_sources.parquet`, `l2_sources.parquet` | One row per source (group of signals) per shot |
| `l1_signals/signals_<shot_id>.parquet`, `l2_signals/signals_<shot_id>.parquet` | One row per signal for a single shot |

`l1_` files describe the level 1 data and `l2_` files describe the level 2 data.

## Loading and filtering

Each file is read whole (the largest is around 15 MB) and filtered with pandas.

```python
import pandas as pd

META_URL = "https://s3.echo.stfc.ac.uk/mast/fairmast-meta"

shots = pd.read_parquet(f"{META_URL}/l2_shots.parquet")

# One shot
shot = shots[shots.shot_id == 30421].iloc[0]

# Every shot in a campaign, with a few columns
m9 = shots[shots.campaign == "M9"]
m9[["shot_id", "timestamp", "preshot_description", "divertor_config"]]

# Number of shots per campaign
shots.groupby("campaign").size()

# Every signal in one shot
signals = pd.read_parquet(f"{META_URL}/l2_signals/signals_30421.parquet")
```

## From metadata to data

Each row's `url` and `endpoint_url` locate the shot's Zarr file. For signals, `source` is the group within it. Opening `s3://` URLs needs `s3fs`.

```python
import xarray as xr

ip = signals[(signals.source == "summary") & (signals.name == "ip")].iloc[0]

ds = xr.open_zarr(
    ip.url,
    group=ip.source,
    storage_options=dict(anon=True, endpoint_url=ip.endpoint_url),
)
ds["ip"]
```

The same file is available over HTTPS at `https://s3.echo.stfc.ac.uk/mast/level2/shots/<shot_id>.zarr` (`level1` for level 1).

## All signals

Signals are stored as one file per shot: 15,969 files for level 1 and 11,573 for level 2. To search signals across all shots, download the folder with [s5cmd](https://github.com/peak/s5cmd) and read it as a single DataFrame:

```bash
s5cmd --no-sign-request --endpoint-url https://s3.echo.stfc.ac.uk \
  cp "s3://mast/fairmast-meta/l2_signals/*" ./l2_signals/
```

```python
signals = pd.read_parquet("./l2_signals")
signals[signals.name == "ip"]
```

See the [Quickstart](quickstart.ipynb) for a runnable introduction and [Bulk Download](bulk_download.ipynb) for more on s5cmd.
