# Release History

Level 2 is regenerated when we fix a problem, replacing files at the same paths,
so the same shot downloaded at different times can differ. Changes are listed
newest first, with what older files contain. For details of each correction, see
[Corrections](corrections.md).

## Which version do you have?

Each level 2 group records when it was produced and from which
[ingestion](https://github.com/ukaea/fair-mast-ingestion) commit:

```python
import xarray as xr

ds = xr.open_zarr("https://s3.echo.stfc.ac.uk/mast/level2/shots/30421.zarr", group="summary")
print(ds.attrs["ingested_at"], ds.attrs["commit_url"])
```

| Release | Ingested | Includes |
| --- | --- | --- |
| **Corrections release** | TBC | Everything on this page |
| **September 2026** | 23–29 September 2026, commit `ed6ea4e` | Changes up to 24 August 2026 |

## Corrections release

% TODO: add the release date once the re-ingest is published.

### Archive corrections

- **CC04 withheld from shot 25366.** Older files: reversed (25470–25793), then dead
  (25794 onwards). See [`magnetics`](corrections.md#magnetics).
- **Saddle coils M02, M08, M012 sign-corrected.** Older files: field reversed from
  24782, voltage reversed up to 24781. See [`magnetics`](corrections.md#magnetics).
- **PF scaling completed** (`SOL` ×0.5, `P6L`/`P6U` ×4). September 2026 files: the
  solenoid is 2× too high and P6 is 4× too low. See
  [`pf_active`](corrections.md#pf_active).

### Fixes to our own processing

#### Samples dropped or misplaced on the time grid

**Affected:** grid-resampled datasets, most visibly `equilibrium`, `magnetics`,
`summary`, `bolometer` and the 50 µs datasets.

Level 2 matched sample times to grid points at floating-point precision, which is
too strict for the archive's approximate times ([Time Bases](time-bases.md)),
especially near *t* = 0. On shot 30421, 18 of 107 `wmhd` slices held the previous
slice's value and two EFIT solutions were dropped (131 of 141 present after the
fix, 129 before). On shot 26399, only 2,293 of 4,200 `pf_active` grid points held
their own sample; now all do.

![Stored energy (wmhd) on shot 30421 before and after the fix. Before, 18 slices carry the previous slice's value and one is missing.](../assets/data-issues/efit-missing-points.png)

*`equilibrium.wmhd`, shot 30421. Before the fix (orange), 18 of 107 slices carried
the previous slice's value and one was missing.*

Matching now uses the sampling step
([#152](https://github.com/ukaea/fair-mast-ingestion/pull/152)). Unaffected
datasets are unchanged.

#### Thomson scattering time axis doubled

**Affected:** 124 of the 1,177 M9 shots with Thomson data: 30073–30210 (almost
all), 29525, 29574–29575, 30040, 30321, 30417–30419, 30421, 30441 and 30443.

The core (`t_e_core`, `n_e_core`) and profile (`t_e`, `n_e`, `p_e`) signals give
times for the same laser pulses that differ by up to 3.9 µs. Merging kept both,
giving 283 time steps for 145 pulses on shot 30421, half of them empty for any
variable.

![Electron temperature on shot 30421 before and after the fix. Before, 283 time steps with 142 empty; after, 145 steps with 4 empty.](../assets/data-issues/thomson-t-e.png)

*Electron temperature at R = 0.90 m, shot 30421, before and after the fix.*

Axes sampled at the same rate are now merged, one step per pulse
([#152](https://github.com/ukaea/fair-mast-ingestion/pull/152)). Empty values on
shot 30421 fall from 57.6% to 16.4%; the rest are channels outside the 0.30–1.49 m
grid. Genuine burst-mode gaps are unaffected: they show in a single signal, while
this fault only appeared after merging.

#### Saddle coil voltage channels empty

**Affected:** the last three channels of `b_field_tor_probe_saddle_voltage`, shots
11708–27619.

Level 2 requested `M10`–`M12`, but the archive names them `M010`–`M012`, so they
were all-NaN. Now read correctly
([#157](https://github.com/ukaea/fair-mast-ingestion/pull/157)).

## Earlier changes

Dates are merge dates. **Correction** fixes archive values; **Processing** changes
how level 2 is produced.

| Merged | Type | Change | Older files |
| --- | --- | --- | --- |
| 2026-08-24 | Processing | Profiles split by shot range take attributes from the right range ([#144](https://github.com/ukaea/fair-mast-ingestion/pull/144)) | `units` and `description` may come from another part of the campaign |
| 2026-08-24 | Processing | EFIT constraint axes named via `n_flux_loop_order` ([#143](https://github.com/ukaea/fair-mast-ingestion/pull/143)) | Unnamed numbered axes |
| 2026-08-18 | Processing | Thomson radial grid ends at 1.49 m ([17f6465](https://github.com/ukaea/fair-mast-ingestion/commit/17f6465)) | 121 radial points, not 120 |
| 2026-08-18 | Processing | Thomson uses the laser's pulse times ([#142](https://github.com/ukaea/fair-mast-ingestion/pull/142)) | Uniform 5 ms grid that smoothed fast events, such as a tearing mode on burst-mode shot 24623 |
| 2026-07-15 | Correction | PF feed currents multiplied by turns ([#129](https://github.com/ukaea/fair-mast-ingestion/pull/129)); also dropped the solenoid's ×0.5 | Per-turn currents; solenoid halved |
| 2026-07-14 | Processing | Saddle field channels `M010`–`M012` read correctly ([#127](https://github.com/ukaea/fair-mast-ingestion/pull/127)) | All-NaN |
| 2026-07-10 | Processing | `shot_id` is a coordinate, not a dimension ([#124](https://github.com/ukaea/fair-mast-ingestion/pull/124)) | Extra length-one `shot_id` dimension |
| 2026-06-01 | Processing | Mistyped Thomson time step fixed to 5 ms ([#120](https://github.com/ukaea/fair-mast-ingestion/pull/120)); superseded by #142 | Step of 5×10⁻³⁵ s |
| 2026-05-22 | Processing | `shot_id` added, so shots can be concatenated ([#98](https://github.com/ukaea/fair-mast-ingestion/pull/98)) | No `shot_id` |
| 2026-05-15 | Processing | All time grids start at −0.1 s ([#111](https://github.com/ukaea/fair-mast-ingestion/pull/111)) | Start follows plasma onset, so axes do not align across shots |
| 2026-05-15 | Processing | `ingested_at` and `commit_url` attributes added ([#113](https://github.com/ukaea/fair-mast-ingestion/pull/113)) | No provenance |
| 2026-05-01 | Processing | Channel coordinates named consistently after UDA signals ([#107](https://github.com/ukaea/fair-mast-ingestion/pull/107)) | Inconsistent channel names |
| 2026-04-27 | Correction | Solenoid halved and moved into `pf_active.coil_current` as `SOL` ([#110](https://github.com/ukaea/fair-mast-ingestion/pull/110)) | Separate `pf_active.solenoid_current`, 2× too high |
| 2026-04-27 | Processing | One wrong-length signal no longer drops the rest of its source ([#102](https://github.com/ukaea/fair-mast-ingestion/pull/102)) | Data may be missing because of one bad signal |
| 2026-03-20 | Processing | Corrupted shots 26958, 26963, 26964, 26967 re-ingested ([issue #105](https://github.com/ukaea/fair-mast-ingestion/issues/105)) | Unreadable |
| 2025-12-18 | Processing | Dataset attributes no longer copied from a variable ([#97](https://github.com/ukaea/fair-mast-ingestion/pull/97)) | For example, `summary` has `units: A` from `ip` |
| 2025-09-08 | Processing | IMAS descriptions added where they exist ([#88](https://github.com/ukaea/fair-mast-ingestion/pull/88)) | No descriptions |
| 2025-06-24 | Processing | X-point channel names and size fixed ([#83](https://github.com/ukaea/fair-mast-ingestion/pull/83)) | Wrong names and size |
| 2025-05-19 | Processing | Valve and target voltages published, with valve group attributes ([#72](https://github.com/ukaea/fair-mast-ingestion/pull/72)); see [`gas_injection`](corrections.md#gas_injection) | No valve data |
| 2025-05-01 | Processing | `pf_active` current and voltage get separate channel dimensions ([#71](https://github.com/ukaea/fair-mast-ingestion/pull/71)) | Both use `channel` |
| 2025-04-08 | Processing | Time is the last dimension in `charge_exchange`, `thomson_scattering`, `equilibrium`, `camera_visible` ([#67](https://github.com/ukaea/fair-mast-ingestion/pull/67)) | Inconsistent dimension order |
| 2025-04-02 | Correction | Saddle voltage offsets subtracted ([#55](https://github.com/ukaea/fair-mast-ingestion/pull/55)) | Offsets included |
