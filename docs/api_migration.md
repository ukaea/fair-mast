# Migrating from the API

The REST and GraphQL APIs at `mastapp.site` have been retired, and the domain no longer points to this service. The metadata they served (shots, sources and signals for level 1 and level 2) is published as Parquet files in the same public S3 bucket as the shot data. No credentials are needed.

- S3: `s3://mast/fairmast-meta/` with endpoint `https://s3.echo.stfc.ac.uk`
- HTTPS: `https://s3.echo.stfc.ac.uk/mast/fairmast-meta/`

The shot data itself has not moved. Each shot is still a Zarr file at `https://s3.echo.stfc.ac.uk/mast/level1/shots/<shot_id>.zarr` or `https://s3.echo.stfc.ac.uk/mast/level2/shots/<shot_id>.zarr`. The `url` column of the shots, sources and signals files gives the same location as an `s3://` path.

## Files

| File | Contents |
|---|---|
| `l1_shots.parquet`, `l2_shots.parquet` | One row per shot: shot metadata and CPF summary statistics |
| `l1_sources.parquet`, `l2_sources.parquet` | One row per source (group of signals) per shot |
| `l1_signals/signals_<shot_id>.parquet`, `l2_signals/signals_<shot_id>.parquet` | One row per signal for a single shot |

The `l1_` files describe the level 1 data and the `l2_` files describe the level 2 data.

## Old endpoints and what replaces them

Endpoints under `/json/level2/...` and `/parquet/level2/...` map to the `l2_` files. The same endpoints without `level2` map to the `l1_` files.

| Old endpoint | Replacement |
|---|---|
| `/json/shots`, `/parquet/shots`, `/ndjson/shots` | `l1_shots.parquet` (`l2_shots.parquet` for level 2) |
| `/json/shots/{shot_id}` | The row of the shots file with that `shot_id` |
| `/json/shots/{shot_id}/signals`, `/parquet/signals?shot_id=...` | `l1_signals/signals_{shot_id}.parquet` |
| `/json/signals`, `/ndjson/signals`, `/parquet/signals?name=...` | All the files in `l1_signals/`, filtered with pandas ([see below](#all-signals)) |
| `/json/signals/{uuid}`, `/json/signals/{uuid}/shot` | The row with that `uuid` in the signals files. Its `shot_id` column identifies the shot. |
| `/json/sources`, `/parquet/sources`, `/ndjson/sources` | `l1_sources.parquet` |
| `/json/sources/{name}`, `/json/level2/sources/{uuid}` | The rows of the sources file with that `name` or `uuid` |
| `/json/scenarios` | The `scenario` and `shot_scenario` columns of the shots files |
| `.../aggregate` endpoints | Group the DataFrame with pandas |
| `/graphql` | The same files. Select the columns you need with pandas. |
| `/json/cpf_summary` | Descriptions of the CPF columns are not yet published in `fairmast-meta/` |

Query strings such as `?filters=campaign$eq:M9`, and cursor-based pagination, are no longer needed. Each file is downloaded whole, the largest being around 15 MB, and then filtered locally.

## Examples

```python
import pandas as pd

META_URL = "https://s3.echo.stfc.ac.uk/mast/fairmast-meta"

shots = pd.read_parquet(f"{META_URL}/l2_shots.parquet")

# Was /json/level2/shots/30421
shot = shots[shots.shot_id == 30421].iloc[0]

# Was /json/level2/shots?filters=campaign$eq:M9
m9 = shots[shots.campaign == "M9"]

# Was a GraphQL query selecting a few fields
m9[["shot_id", "timestamp", "preshot_description", "divertor_config"]]

# Was /json/level2/shots/aggregate (e.g. number of shots per campaign)
shots.groupby("campaign").size()

# Was /json/level2/shots/30421/signals
signals = pd.read_parquet(f"{META_URL}/l2_signals/signals_30421.parquet")
```

(all-signals)=
### All signals

Signals are stored as one file per shot: 15,969 files for level 1 and 11,573 for level 2. To search signals across all shots, download the folder with [s5cmd](https://github.com/peak/s5cmd) and read it as a single DataFrame:

```bash
s5cmd --no-sign-request --endpoint-url https://s3.echo.stfc.ac.uk \
  cp "s3://mast/fairmast-meta/l2_signals/*" ./l2_signals/
```

```python
signals = pd.read_parquet("./l2_signals")

# Was /parquet/level2/signals?name=ip
signals[signals.name == "ip"]
```

See the [Quickstart](quickstart.ipynb) for a runnable introduction and [Bulk Download](bulk_download.ipynb) for more on using s5cmd.
