# Time Bases

UDA does not store when each sample was taken. It rebuilds the times, often in
single precision, so they are close to but not exactly the sampled times. This
affects every source.

## How UDA stores time

Most signals are stored as a start, a step and a count, and the axis is rebuilt on
every read:

*t*<sub>k</sub> = start + *k* &times; step

With the start and step in float32 (about seven significant figures), the result
is approximate:

| Comparison | Typical difference |
| --- | --- |
| Two signals sampling the same instants, built by different routes | Up to about 4 µs |
| One signal read by two builds of the UDA client | About 0.06 µs |
| A float64 axis against the decimal times it describes | A few picoseconds |

## What affects the error

| Factor | Effect |
| --- | --- |
| **Precision** | float64 is accurate to picoseconds; float32 is not. It varies by shot: `XDC_PF_F_P1` is float64 on M9 and float32 earlier. |
| **Distance along the axis** | The error grows with *k*. The plasma current starts at −2 s, about 10,000 steps before the plasma. |
| **Step rounding** | Steps of 0.25, 0.5 and 1 ms are stored slightly large and drift *late*; 0.2 ms, 5 ms and microsecond steps drift *early*. |
| **Start time** | Changes which samples are affected. From about shot 27880 the plasma current starts at −2.0000002 s, which avoids the problem for that signal; the bolometer is affected on every shot measured. |
| **Client build** | x86-64 and Apple arm64 expand the recipe differently: 15,828 of 30,000 plasma current samples differ on shot 26000. All level 2 data was read with x86-64. |
| **EFIT time slices** | Stored as a float32 list rather than a recipe: 0.07 s becomes 0.07000000029802322 s, and 16 of 45 slices on shot 30471 sit just after their nominal time. |

Reading in double precision fixes recipe axes (late samples on shots 11766, 22000
and 26000 drop from 396, 396 and 2,134 to zero), but not EFIT's lists, which the
archive appears to hold only in float32.

## Why it matters

The errors are far smaller than any sampling interval, but they break exact time
matching. A lookup such as "latest sample at or before *t*" can pick the previous
sample: an error of one whole sample.

## Analysed data in the archive

Analysed products, such as EFIT (`EFM`) and the analysed magnetics (`ASM`), were
computed from these time axes. Where an analysis code matched times exactly, for
example to pick EFIT's inputs at each time slice, it may have used a sample one
interval early or late. This cannot be checked or corrected, because the codes are
not in the archive. Treat their timing as uncertain to one sampling interval of
their inputs.

## What we did

- Wrote it up for the UDA team, with a reproducible example.
- Level 2 treats times within a quarter of a sampling step as the same instant,
  moves samples only to the nearest grid point, and merges time axes only if they
  were sampled at the same rate.

Earlier versions of level 2 dropped or misplaced samples near *t* = 0, shifted
EFIT slices and doubled Thomson time axes; see
[Release History](release-history.md#fixes-to-our-own-processing).

## How level 2 handles time

All datasets except `thomson_scattering` and `wall` are resampled onto a uniform
grid from −0.1 s (−0.01 s for `spectrometer_visible`) with a zero-order hold: each
grid point takes the most recent sample at or before it.

| Dataset | Grid step |
| --- | --- |
| `equilibrium`, `charge_exchange` | 5 ms |
| `summary` | 1 ms |
| `bolometer` | 0.5 ms |
| `magnetics`, `pf_passive`, `tf` | 0.2 ms |
| `pulse_schedule`, `controllers`, `gas_injection`, `pf_active` | 50 µs |
| `interferometer`, `spectrometer_visible` | 20 µs |
| `soft_x_rays` | 2 µs |

Some datasets have extra, finer time axes, such as `time_saddle` in `magnetics`.

- Grid times are exact; a change can appear up to one step late.
- Data before the grid start is not published. About 95% of shots have plasma
  onset between −0.13 s and −0.04 s; the earliest is −0.92 s.
- Thomson scattering keeps the laser pulse times from UDA.

## What this means for you

- Compare times from UDA, and Thomson times, with a tolerance, not for equality.
- Expect diagnostics to line up only to a few microseconds at their native rates.
- Treat the timing of analysed products, including EFIT, as uncertain to one
  sampling interval of their inputs.
