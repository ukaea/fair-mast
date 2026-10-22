# Corrections

Every change level 2 makes to the values in the MAST archive, grouped by UDA
source. The data files do not flag these changes: this page is the record. See
also [Time Bases](time-bases.md) and [Release History](release-history.md).

Some values in the archive are wrong at source. Level 2 corrects them, so it can
deliberately differ from UDA.

## Policy

| Action | When |
| --- | --- |
| **Correct** | The cause is established, the true value is known independently, and the result can be checked against unaffected channels |
| **Withhold** (publish NaN) | The value is clearly wrong but the correct value is unknown |
| **Keep** | The value records what a calculation was given, such as EFIT's inputs. Kept even when wrong. |

## Summary

| Source | Level 2 data | Correction | Shots |
| --- | --- | --- | --- |
| [AMB](#amb-flux-loops) | `magnetics.flux_loop_flux`, `CC04` | Withheld | 25366 onwards |
| [EFM](#efm-efit) | `equilibrium.flux_loop_measured`, index 3 | Kept | 25470–25793 |
| [EFM](#efm-efit) | `equilibrium` | Missing values are NaN, not −999 | All |
| [ASM](#asm-saddle-coil-field) | `magnetics.b_field_tor_probe_saddle_field`, `M02`, `M08`, `M012` | Sign reversed | 24782–30473 |
| [XMB](#xmb-saddle-coil-voltage) | `magnetics.b_field_tor_probe_saddle_voltage`, `M02`, `M08`, `M012` | Sign reversed | 11708–24781 |
| [XMB](#xmb-saddle-coil-voltage) | `magnetics.b_field_tor_probe_saddle_voltage` | Offset subtracted | 11708–30473 |
| [AMC](#amc-pf-coil-currents) | `pf_active.coil_current` | Scaled to coil current | All |
| [XMC](#xmc-mirnov-coils) | `magnetics.b_field_tor_probe_cc_field`, `b_field_pol_probe_cc_field` | Scaled to tesla | All |

## Scale factors

| Source | Channels | Factor | Shots | Reason |
| --- | --- | --- | --- | --- |
| AMC | `SOL` | ×0.5 | All | Parallel feed reads twice the coil current |
| AMC | `P2IL FEED`, `P2IU FEED` | ×12 | All | Current stored per turn |
| AMC | `P2OL FEED`, `P2OU FEED`, `P3L FEED`, `P3U FEED` | ×8 | All | Current stored per turn |
| AMC | `P4L FEED`, `P4U FEED`, `P5L FEED`, `P5U FEED` | ×23 | All | Current stored per turn |
| AMC | `P6L`, `P6U` | ×4 | All | Current stored per turn |
| XMC | Every channel of `b_field_tor_probe_cc_field`, `b_field_pol_probe_cc_field` | ×2×10⁻⁶ | All | Voltage to tesla |
| ASM | `M02`, `M08`, `M012` | ×−1 | 24782–30473 | Stale sign flip |
| XMB | `M02`, `M08`, `M012` | ×−1 | 11708–24781 | Wiring reversal |

Unit conversions declared in the archive (such as kA to A) are not listed.

## AMB: flux loops

### CC04 withheld from shot 25366

| Field | Value |
| --- | --- |
| **UDA signal** | `AMB_FL/CC04` |
| **Level 2 data** | `magnetics.flux_loop_flux`, channel `CC04` |
| **Shots** | 25366 onwards |
| **Correction** | Withheld (NaN) |
| **Introduced** | [#155](https://github.com/ukaea/fair-mast-ingestion/pull/155) |

**Problem.** On shots 25470–25793, CC04 reads with its sign reversed relative to
the other centre column loops (CC03, CC05, CC07, CC09): slope −1.000, correlation
−0.9997 over 183 shots. From 25794 it is dead, flat at about 6&times;10⁻⁵ Wb. The
reversal is in every archive copy of CC04, including EFIT's inputs.

**Assumptions.**

- The cause is unknown, so the sign may not be the only error. We withhold rather
  than flip.
- The last good shot is 25365 and the first reversed is 25470; nothing in between
  has plasma. We withhold from 25366.
- 141 of the 324 shots in 25470–25793 have no plasma or no CC04 data, so the whole
  window is treated as suspect.

**Fix.** CC04 is NaN from 25366. It keeps its place on `flux_loop_channel`, so the
array shape does not change.

**Impact.** Use NaN-aware reductions. The original values are unchanged in UDA
(`AMB_FL/CC04`). For earlier shots, see [Known limitations](#known-limitations).

## EFM: EFIT

### CC04 kept in EFIT's inputs

| Field | Value |
| --- | --- |
| **UDA signal** | `EFM_SILOP_(X)` |
| **Level 2 data** | `equilibrium.flux_loop_measured`, index 3 of `n_flux_loop` |
| **Shots** | 25470–25793 |
| **Correction** | None |

Index 3 holds the reversed CC04 values EFIT was given. They are kept as a record
of the fit's inputs; use `n_flux_loop_order` to exclude them.
`flux_loop_reconstructed` is unaffected. EFIT's flux loop weights and χ²
(`EFM_FWTSI`, `EFM_SILOP_CHISQ`) are zero on these shots, so whether EFIT used CC04
is unknown, and equilibria in this range may be affected.

### Missing values are NaN, not −999

| Field | Value |
| --- | --- |
| **UDA signal** | EFIT data (`EFM`) |
| **Level 2 data** | `equilibrium` |
| **Shots** | All |
| **Correction** | Missing values are NaN |

Some archive EFIT data marks missing values as −999, which looks like a real
value. Level 2 uses NaN; a check of ten shots (15000–30421) found no −999. Treat
−999 as missing if you read EFIT data from UDA.

## ASM: saddle coil field

### M02, M08 and M012 sign-corrected

| Field | Value |
| --- | --- |
| **UDA signal** | `ASM_SAD/M02`, `ASM_SAD/M08`, `ASM_SAD/M012` |
| **Level 2 data** | `magnetics.b_field_tor_probe_saddle_field`, channels `M02`, `M08`, `M012` |
| **Shots** | 24782–30473 |
| **Correction** | ×−1 |
| **Introduced** | [#157](https://github.com/ukaea/fair-mast-ingestion/pull/157) |

**Problem.** These coils were wired backwards, and UDA's analysis (`ASM_SAD`)
compensated with a fixed sign flip. The wiring was repaired between shots 24742
and 24783, but the flip stayed, so `ASM_SAD` is reversed from then on. The raw
signal (`XMB_SAD`) flips at the same point:

```text
shot    | raw   M02   M08   M12 | analysed M02   M08   M12
24736   | -1.04 -1.00 -1.09     | +1.03 +0.99 +1.00    analysis flip correct
24741   | -1.03 -1.01 -1.07     | +1.03 +0.99 +1.00
        |   ---- wiring repaired somewhere in 24742-24783 ----
24785   | +1.02 +0.98 +1.01     | -1.19 -1.07 -0.97    analysis flip now wrong
```

*Each coil regressed on the median of the others: +1 agrees, −1 reversed.*

Across the 12,778 shots with `ASM_SAD`, only these three coils stand out:

| Channel | Shots reversed | Shots correct |
| --- | --- | --- |
| M02 | 814 | 4409 |
| M08 | 825 | 4330 |
| M012 | 815 | 4427 |
| Every other coil | 40 or fewer (noise) | about 5250 |

**Assumptions.** The analysed data is correct before 24782 and reversed from 24785,
with no usable data in between. The sign is the only error: once corrected, the
three coils agree with the eight unaffected ones.

**Fix.** ×−1 for shots 24782–30473; earlier shots unchanged.

**Impact.** Differs from `ASM_SAD` by a sign over 24782–30473.

### UDA signals derived from these coils

These are not published. Recompute them from the corrected coils.

- `ASM_SAD/D02 2-8`: both coils reversed, so the result is negated. Flip its sign.
- `ASM_SAD/D05 6-12`: one coil reversed, so from 24785 it is a sum, not a
  difference (amplitude relative to one coil jumps from about 0.2 to 2.1). Not
  recoverable from the channel alone.
- `ASM_OUT` (locked mode detector: `SIGNAL`, `THETA`, `THETA_DEVIATION`, `RATING`,
  `NN_RATING`, `NN_PATTERN`): every output changes at 24785. `RATING` is pinned at
  its maximum on about 71% of shots after, against 7% before. We cannot rule out
  that the detector itself also changed.

```{warning}
Results based on the saddle coils or the locked mode detector for shots from 24785
onwards are worth re-checking.
```

## XMB: saddle coil voltage

### M02, M08 and M012 sign-corrected

| Field | Value |
| --- | --- |
| **UDA signal** | `XMB_SAD/OUT` |
| **Level 2 data** | `magnetics.b_field_tor_probe_saddle_voltage`, channels `M02`, `M08`, `M012` |
| **Shots** | 11708–24781 |
| **Correction** | ×−1 |
| **Introduced** | [#157](https://github.com/ukaea/fair-mast-ingestion/pull/157) |

The raw voltages record the backward wiring, so they are reversed *before* the
repair: the opposite range to the [field](#asm-saddle-coil-field). This profile is
already processed (offset subtracted, below), so it is corrected to the field's
sign convention. Differs from `XMB_SAD` by a sign over 11708–24781.

### Offset subtracted

| Field | Value |
| --- | --- |
| **UDA signal** | `XMB_SAD/OUT` |
| **Level 2 data** | `magnetics.b_field_tor_probe_saddle_voltage`, every channel |
| **Shots** | 11708–30473 |
| **Correction** | Mean of the first ten samples subtracted |
| **Introduced** | [#55](https://github.com/ukaea/fair-mast-ingestion/pull/55) |

The raw voltages sit on an offset. Level 2 subtracts the mean of each channel's
first ten samples, assuming they precede the plasma and the offset is constant;
any drift remains. Differs from `XMB_SAD` by a constant per channel.

## AMC: PF coil currents

### Scaled to the coil current

| Field | Value |
| --- | --- |
| **UDA signal** | `AMC_SOL CURRENT`, `AMC_P2IL FEED CURRENT` and the other PF coil currents |
| **Level 2 data** | `pf_active.coil_current` |
| **Shots** | All |
| **Correction** | Fixed factor per channel (see [Scale factors](#scale-factors)) |
| **Introduced** | [#110](https://github.com/ukaea/fair-mast-ingestion/pull/110), [#129](https://github.com/ukaea/fair-mast-ingestion/pull/129), [#153](https://github.com/ukaea/fair-mast-ingestion/pull/153) |

**Problem.** The archive stores feed currents per turn, with wrong declared units;
used unscaled, they give wrong equilibria. The solenoid's parallel feed reads twice
its coil current.

**Fix.** Each coil is multiplied by its number of turns (12 for P2 inner, 8 for P2
outer and P3, 23 for P4 and P5, 4 for P6) and the solenoid is halved. Checked
against EFIT's PF current inputs, and by re-running FreeGSNKE on a case that failed
unscaled.

**Impact.** The factors came in over three changes, so older files may be scaled
differently. See [Release History](release-history.md).

## XMC: Mirnov coils

### Scaled to tesla

| Field | Value |
| --- | --- |
| **UDA signal** | `XMC/CC/MT`, `XMC/CC/MV` |
| **Level 2 data** | `magnetics.b_field_tor_probe_cc_field`, `magnetics.b_field_pol_probe_cc_field` |
| **Shots** | All |
| **Correction** | ×2×10⁻⁶ |

The archive stores these as raw voltages; level 2 multiplies by 2×10⁻⁶ to give
tesla. The factor's origin is undocumented and unverified, so treat absolute
magnitudes with caution. Shape and timing are unaffected.

## XDC: gas injection

`valve_voltage` is the voltage on each valve; `valve_target_voltage` is the target
waveform for each valve group, `G1`–`G12`. The archive's valve set changes over
MAST, so `valve_voltage` has different channels by shot range:

| Shots | `valve_voltage` channels |
| --- | --- |
| 1–25911 | 12, by target group: `G1`–`G12` |
| 25912–26755 | 19 valves, including `HM12`, `HEOA`, `HEOB` |
| 26756–28355 | 18: `HM12` split into `HM12A`, `HM12B`; no `HEOA`, `HEOB` |
| 28356–30471 | 20: as above plus `HEOA`, `HEOB`, always empty |

From 28356, labels in both variables are lower case (`tc5a`, `g1`). No data for
shots 25912–25936 or 28356–28451.

**Targets and valves.** From 25912, `valve_voltage` has `fuelling_groups` and
`impurity_groups` attributes mapping each target to its valves. The mapping comes
from MAST operations records, not the data.

| Target | Valves | Kind |
| --- | --- | --- |
| `G1` | `TC5A`, `TC5B`, `TC11` | Fuelling |
| `G2` | `BC5` | Fuelling |
| `G3` | `HL1`, `HU6`, `HU8` | Fuelling |
| `G4` | `HU11` | Fuelling |
| `G5` | `HL11` | Impurity |
| `G6` | `BC11` | Impurity |
| `G7` | `HECC` | Impurity |
| `G8` | `HEOA`, `HEOB` (obsolete) | Impurity |
| `G9` | `HM12`, or `HM12A` and `HM12B` | Impurity |
| `G10` | `IBIL` | Impurity |
| `G11` | `IBFUA`, `IBFUB` | Fuelling |
| `G12` | `IBFLA`, `IBFLB` | Fuelling |

The attributes are JSON with full UDA names; channel labels are the last part of
each name:

```python
import json
import xarray as xr

gas = xr.open_zarr("https://s3.echo.stfc.ac.uk/mast/level2/shots/30421.zarr", group="gas_injection")
groups = json.loads(gas.valve_voltage.attrs["fuelling_groups"])
label = lambda name: name.replace("/", "_").split("_")[-1]

valves = groups["/xdc/gas/t/g1"]   # ["/xdc/gas/f/tc5a", "/xdc/gas/f/tc5b", "/xdc/gas/f/tc11"]
gas.valve_voltage.sel(valve_channel=[label(v) for v in valves])
```

**Empty targets.**

- Fuelling targets (`G1`–`G4`, `G11`, `G12`) on many shots, consistent with
  fuelling mode, where the valves share one flow request.
- `G8` from about shot 27300 (obsolete HEO valves).
- All targets from about shot 25800 to 27200; cause unknown.

The `ECEL` and `HFS` valves are intermittent and not published.

## Known limitations

Not fixed at the time of writing.

| Data | Limitation |
| --- | --- |
| `b_field_tor_probe_saddle_field`, `M09` | Empty: there is no `ASM_SAD/M09`. An all-NaN channel means the signal is missing, not that the diagnostic was off. |
| `b_field_tor_probe_saddle_voltage` | The last three channels are `M010`–`M012` up to shot 27619 and `M10`–`M12` from 27620, following the archive |
| `flux_loop_flux`, `CC04` | Intermittently dead on 792 shots in 22372–25365, published as near-zero noise rather than NaN |
| `flux_loop_flux` | 15 of the 19 loops in `AMB_FL`; `P2L/1`, `P3L/1`, `P5U/4` and `P6U/1` are missing, though EFIT uses them |
| Flux loop `P5L/3` | Position (R = 1.7463 m, Z = −0.5322 m) does not mirror `P5U/3` (about 1.55 m, −0.564 m). Any error is in the source geometry. |
| `equilibrium.beta_pol` | EFIT's definition (boundary poloidal field), but the description gives the IMAS one, 4∫p dV / (R₀ μ₀ I<sub>p</sub>²), which is about 20% lower (shot 30039, 0.3 s: 0.61 against 0.49). [#158](https://github.com/ukaea/fair-mast-ingestion/issues/158) |
| Thomson scattering radius | `AYC_R` drifts up to 1.8 cm within a shot but is taken from the first time step |
| `bolometer.power` | Declared in W/m², but IMAS types it in W; unresolved |
| Not published | Halo currents (`AMH`); most Mirnov channels (3 in `b_field_pol_probe_omv_voltage`, 3 in `b_field_tor_probe_cc_field`, 5 in `b_field_pol_probe_cc_field`) |

## Reporting a problem

Open an issue on [fair-mast](https://github.com/ukaea/fair-mast/issues) with the
signal, shot range and what you expected.
