# Time Bases

The MAST archive does not store the time at which each sample was taken. It
stores enough to rebuild it, often in single precision, so the times UDA returns
are close to, but not exactly, the times a diagnostic sampled. This affects every
source, by different amounts. This page explains how, what makes it better or
worse, what it means for the archive's analysed data, and how level 2 handles it.

## How UDA stores time

For most signals UDA stores a recipe: a start time, a step and a number of
samples. The time axis is rebuilt from it every time the data is read:

*t*<sub>k</sub> = start + *k* &times; step

The start and step are often held in single precision (float32), which carries
about seven significant figures, and the rebuilt times inherit that limit.
Typical sizes of the resulting differences:

| Comparison | Typical difference |
| --- | --- |
| Two signals describing the same instants, built by different routes | Up to about 4 µs |
| The same signal read by two different builds of the UDA client | About 0.06 µs |
| A double-precision (float64) axis against the decimal times it describes | A few picoseconds |

## What makes it better or worse

| Factor | Effect |
| --- | --- |
| **Precision of the stored axis** | A float64 axis is accurate to a few picoseconds; a float32 axis is not. The precision is not fixed per signal: `XDC_PF_F_P1`, for example, is float64 on M9 shots and float32 on earlier shots. |
| **Distance along the axis** | The error grows with *k*, so it is worst at the far end of long axes. The plasma current, for example, starts at −2 s, so by the time of the plasma its rebuilt time has accumulated about 10,000 steps. |
| **Whether the step rounds up or down** | Most decimal steps have no exact float32 value. Steps of 0.25 ms, 0.5 ms and 1 ms are stored slightly too large, so their times drift progressively *late*. Steps of 0.2 ms, 5 ms and the microsecond steps are stored slightly too small and drift *early*. |
| **The start time** | It changes which samples are affected. From about shot 27880 the plasma current (`AMC_PLASMA CURRENT`) starts at −2.0000002 s rather than −2 s, which happens to avoid the problem for that signal. This is a property of the signal, not of the shot: the bolometer is affected on every shot we measured, including the late ones. |
| **The UDA client build** | The same recipe is expanded with slightly different arithmetic on different processors. For the plasma current on shot 26000, the x86-64 and Apple arm64 builds disagree on 15,828 of 30,000 samples. All published level 2 data was read with the same x86-64 build. |
| **EFIT time slices** | EFIT stores an explicit list of times rather than a recipe, but in float32. 0.07 s, for example, is stored as 0.07000000029802322 s, so on shot 30471, 16 of 45 slices sit fractionally after their nominal time. |

Reading the axes in double precision fixes the recipe case: on shots 11766, 22000
and 26000, the number of samples that land after their true time goes from 396,
396 and 2,134 to zero. It does not help EFIT's lists, which the archive appears to
hold only in single precision.

## Why such small errors matter

These errors are tiny compared with any sampling interval, so on their own they
do not change a value. They matter when software needs to decide whether two
times are *the same*, for example when it takes "the latest sample at or before"
some time. If a sample's rebuilt time falls just after that time when the true
time was just before it, the sample is skipped and the previous one is used
instead: an error of one whole sample, not of a few nanoseconds.

## Analysed data in the archive

Many signals in the archive are themselves analysed products, computed by MAST's
analysis codes from the raw measurements: the EFIT equilibria (`EFM`), the
analysed magnetics (`ASM`) and others. Those codes worked with the archive's time
axes. Wherever one of them matched times exactly, for example to pick the
measurements EFIT was given at each time slice, it may occasionally have used the
neighbouring sample: one sampling interval early or late.

We cannot check whether this happened, or correct it if it did. The analysis
codes are not part of the archive, and their results are stored as they were
produced. The effect is limited to at most one sampling interval of the input
signal, and it only matters for quantities that change significantly within one
interval. Treat the timing of analysed products as uncertain at that level.

## What we did

- **Written it up for the UDA team**, with a reproducible example. MAST is no
  longer maintained, so we do not expect a change upstream.
- **Level 2 no longer relies on times matching exactly.** When it places samples
  on its uniform time grid, two times count as the same instant if they are within
  a quarter of the sampling step, and a sample can only move to the grid point
  nearest to it. Time axes from the same diagnostic are only treated as the same
  if they were sampled at the same rate.

Earlier versions of level 2 did not allow for this. Samples near *t* = 0 were
dropped or placed on the wrong grid point, some EFIT time slices carried the
previous slice's values, and Thomson scattering time axes were doubled. Those
were bugs in our processing and are fixed; see
[Release History](release-history.md#fixes-to-our-own-processing).

## How level 2 handles time

Every level 2 dataset except `thomson_scattering`, `camera_visible` and `wall` is
resampled onto a uniform time grid that starts at **−0.1 s** (−0.01 s for
`spectrometer_visible`). Each grid point carries the most recent sample at or
before it (a zero-order hold), not an interpolation between samples.

| Dataset | Time grid step |
| --- | --- |
| `equilibrium`, `charge_exchange` | 5 ms |
| `summary` | 1 ms |
| `bolometer` | 0.5 ms |
| `magnetics`, `pf_passive`, `tf` | 0.2 ms |
| `pulse_schedule`, `controllers`, `gas_injection`, `pf_active` | 50 µs |
| `interferometer`, `spectrometer_visible` | 20 µs |
| `soft_x_rays` | 2 µs |

Some datasets have further time axes at finer steps, such as `time_saddle` in
`magnetics`. So:

- **Times on the level 2 grid are exact.** Each value is the most recent sample
  at or before its grid time, so a change can appear up to one grid step late.
- **Data before the grid start is not published.** About 95% of shots have plasma
  onset between −0.13 s and −0.04 s; the earliest found is −0.92 s. Those shots
  lose their early history.
- **Thomson scattering is not resampled in time.** Its times are the laser pulse
  times as UDA returns them.

## What this means for you

- **In Thomson scattering, and in anything you read from UDA directly,** times are
  as UDA returns them. Compare times with a tolerance, such as a fraction of the
  sampling step, never for exact equality.
- **Do not expect two diagnostics to line up to better than a few microseconds**
  at their native rates, even when they sampled the same instants.
- **Treat the timing of the archive's analysed products,** including EFIT, as
  uncertain by up to one sampling interval of their inputs.
