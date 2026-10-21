# Corrections

Level 2 data is not always identical to the MAST archive. This page lists every
correction we make to the values the archive holds: what was wrong with them,
what we assumed, and what we did. Corrections are grouped by the UDA source the
data comes from.

The archive's time axes have a problem of their own, which affects every source;
it is described in [Time Bases](time-bases.md). For when each correction was
introduced, and for fixes to our own processing, see
[Release History](release-history.md).

Wherever a value has been changed or withheld, the affected variable carries an
attribute saying so: `cc04_blanked`, `cc04_warning` or `corrected_channels`.

## Why level 2 can differ from UDA

MAST data is no longer maintained upstream, so faults in the archive will not be
fixed at source. Where we are confident of both the cause and the correct value,
we correct the data rather than pass a known fault through. That means **level 2
can deliberately differ from what you get by reading the same signal from UDA**.
Every such case is listed below, with the shots affected.

## How we decide what to do

Two of the faults below look the same in a plot, a channel that suddenly reads
with its sign reversed, and we handled them in opposite ways. The rules:

| Rule | When it applies |
| --- | --- |
| **Correct** | The cause is established, the true value is known from an independent source, and the corrected value can be checked against channels that were not affected |
| **Withhold** | The value is clearly wrong, but we cannot establish what it should be. It is published as NaN. |
| **Keep** | The value is a record of what a calculation was given, such as EFIT's inputs. It is kept as it was, even when wrong, because it explains the result, and it carries a warning attribute. |

## Summary

| Source | Level 2 data | Correction | Shots |
| --- | --- | --- | --- |
| [AMB](#amb-flux-loops) | `magnetics.flux_loop_flux`, `CC04` | Withheld | 25366 onwards |
| [EFM](#efm-efit) | `equilibrium.flux_loop_measured`, index 3 | Kept, with a warning | 25470–25793 |
| [EFM](#efm-efit) | `equilibrium` | Missing values are NaN, not −999 | All |
| [ASM](#asm-saddle-coil-field) | `magnetics.b_field_tor_probe_saddle_field`, `M02`, `M08`, `M012` | Sign reversed | 24782–30473 |
| [XMB](#xmb-saddle-coil-voltage) | `magnetics.b_field_tor_probe_saddle_voltage`, `M02`, `M08`, `M12` | Sign reversed | 11708–24781 |
| [XMB](#xmb-saddle-coil-voltage) | `magnetics.b_field_tor_probe_saddle_voltage` | Offset subtracted | 11708–30473 |
| [AMC](#amc-pf-coil-currents) | `pf_active.coil_current` | Scaled to the coil current | All |
| [XMC](#xmc-mirnov-coils) | `magnetics.b_field_tor_probe_cc_field`, `b_field_pol_probe_cc_field` | Scaled to tesla | All |

## Scale factors

Every fixed factor level 2 applies to the archive's values:

| Source | Channels | Factor | Shots | Reason |
| --- | --- | --- | --- | --- |
| AMC | `SOL` | ×0.5 | All | The solenoid's parallel feed reads twice the coil current |
| AMC | `P2IL FEED`, `P2IU FEED` | ×12 | All | Current stored per turn |
| AMC | `P2OL FEED`, `P2OU FEED`, `P3L FEED`, `P3U FEED` | ×8 | All | Current stored per turn |
| AMC | `P4L FEED`, `P4U FEED`, `P5L FEED`, `P5U FEED` | ×23 | All | Current stored per turn |
| AMC | `P6L`, `P6U` | ×4 | All | Current stored per turn |
| XMC | `b_field_tor_probe_cc_field`, `b_field_pol_probe_cc_field`, every channel | ×2×10⁻⁶ | All | Converts the stored signal to tesla |
| ASM | `M02`, `M08`, `M012` | ×−1 | 24782–30473 | Undo a stale sign flip |
| XMB | `M02`, `M08`, `M12` | ×−1 | 11708–24781 | Undo a wiring reversal |

Level 2 also converts between units where the archive declares them, for
example from kA to A. Those conversions change the number but not the quantity,
and are not listed here.

## AMB: flux loops

### Flux loop CC04 is withheld from shot 25366

| Field | Value |
| --- | --- |
| **UDA signal** | `AMB_FL/CC04` |
| **Level 2 data** | `magnetics.flux_loop_flux`, channel `CC04` |
| **Shots** | 25366 onwards |
| **Correction** | Withheld: published as NaN |
| **Recorded in** | `cc04_blanked` attribute |
| **Introduced** | [#155](https://github.com/ukaea/fair-mast-ingestion/pull/155) |

**What was wrong.** CC04 is one of the centre column flux loops. From shot 25470
to 25793 it reads with its sign reversed relative to the other centre column loops
(CC03, CC05, CC07, CC09): the amplitude is right, the direction is not. Regressing
CC04 on the median of its neighbours over the 183 affected shots gives a slope of
−1.000 and a correlation of −0.9997, a clean polarity flip rather than a gain
error. From shot 25794 it is dead, sitting flat at around 6&times;10⁻⁵ Wb for the
rest of MAST.

| Shots | CC04 |
| --- | --- |
| Up to 25365 (M5–M7) | Correct, but intermittently dead from 22372 |
| 25470–25793 (early M8) | Reversed |
| 25794 onwards (rest of M8, all of M9) | Dead |

The reversed values appear everywhere CC04 is recorded in the archive, including
the inputs EFIT was given (see [EFM](#efm-efit)).

**What we assumed.**

- **The cause is unknown.** It looks as if the loop was re-terminated with
  reversed polarity between M7 and M8 and then failed, but we have not
  established that. Without a cause we cannot be sure that the sign is the only
  thing wrong, so we withhold the values rather than flip them.
- **Where the fault starts.** The last shot where CC04 agrees with its neighbours
  is 25365 and the first reversed shot is 25470. The shots in between have no
  plasma, so the change cannot be pinned more closely. We withhold from 25366.
- **The reversed window is treated as a whole.** Of the 324 shots in 25470–25793,
  141 have no plasma or no CC04 record, so there is nothing to judge them by. We
  treat the whole window as suspect.

**What we did.** CC04 is published as NaN for every shot from 25366. The channel
keeps its place on the `flux_loop_channel` axis, so the shape of the data does not
change partway through the campaign: CC04 is simply empty.

**What this means for you.**

- Shots up to 25365: CC04 is unchanged and usable, except on the intermittently
  dead shots listed under [Known limitations](#known-limitations).
- Shots from 25366: CC04 is NaN. NaN-aware reductions such as `np.nanmean` will
  handle it; plain reductions will propagate NaN.
- If you need the original values, read `AMB_FL/CC04` from UDA. They are
  unchanged there: we have withheld them, not altered them.

## EFM: EFIT

### CC04 in EFIT's inputs is kept, with a warning

| Field | Value |
| --- | --- |
| **UDA signal** | `EFM_SILOP_(X)` |
| **Level 2 data** | `equilibrium.flux_loop_measured`, index 3 of `n_flux_loop` |
| **Shots** | 25470–25793 |
| **Correction** | None: kept as it was |
| **Recorded in** | `cc04_warning` attribute |
| **Introduced** | [#155](https://github.com/ukaea/fair-mast-ingestion/pull/155) |

EFIT was given the same reversed CC04 values described under
[AMB](#amb-flux-loops), and they are stored as the flux loop constraint at index 3
of the 46-element `n_flux_loop` axis.

**We have not withheld these.** The array records what the EFIT reconstruction was
actually given, so blanking it would remove the data needed to explain the
equilibrium that came out. The `n_flux_loop_order` attribute names the loop at
each index, so you can exclude index 3 yourself if you are treating these as
measurements rather than as a record of the fit's inputs.

`equilibrium.flux_loop_reconstructed` is unaffected: it is the fit's output rather
than a measurement, and CC04 there tracks the other loops normally.

Equilibria for shots 25470–25793 may themselves be affected. EFIT's stored
weights and χ² for the flux loops (`EFM_FWTSI`, `EFM_SILOP_CHISQ`) are zero for
every loop on these shots, so the archive does not record whether EFIT used CC04.

### Missing values are NaN, not −999

| Field | Value |
| --- | --- |
| **UDA signal** | EFIT data (`EFM`) |
| **Level 2 data** | `equilibrium` |
| **Shots** | All |
| **Correction** | Missing values are NaN |

**What was wrong.** Some of the archive's EFIT data marks missing values with
−999 rather than leaving them empty. A −999 is easy to mistake for a real value:
plotted, it shows as a large spike, and it distorts any average it is included in.

**What we did.** In level 2, missing EFIT values are NaN. We checked `equilibrium`
on ten shots from across MAST, from 15000 to 30421, and found no −999 values.

**What this means for you.** If you read EFIT data from UDA directly, treat −999
as missing.

## ASM: saddle coil field

### Saddle coils M02, M08 and M012 are sign-corrected

| Field | Value |
| --- | --- |
| **UDA signal** | `ASM_SAD/M02`, `ASM_SAD/M08`, `ASM_SAD/M012` |
| **Level 2 data** | `magnetics.b_field_tor_probe_saddle_field`, channels `M02`, `M08`, `M012` |
| **Shots** | 24782–30473 |
| **Correction** | Multiplied by −1 |
| **Recorded in** | `corrected_channels` attribute |
| **Introduced** | [#157](https://github.com/ukaea/fair-mast-ingestion/pull/157) |

**What was wrong.** Three of the twelve outboard saddle coils were physically
wired backwards for most of MAST's life. UDA's analysed product, `ASM_SAD`,
compensated by flipping their sign. The wiring was then repaired, but the flip was
never removed, so from that point on the analysed values are reversed. The fault
is in the analysis step that produced `ASM_SAD`, not in the measurement.

```text
shot    | raw   M02   M08   M12 | analysed M02   M08   M12
24736   | -1.04 -1.00 -1.09     | +1.03 +0.99 +1.00    analysis flip correct
24741   | -1.03 -1.01 -1.07     | +1.03 +0.99 +1.00
        |   ---- wiring repaired somewhere in 24742-24783 ----
24785   | +1.02 +0.98 +1.01     | -1.19 -1.07 -0.97    analysis flip now wrong
```

*Each coil regressed on the median of the other coils: +1 means it agrees with
them, −1 means it is reversed. "Raw" is `XMB_SAD`, "analysed" is `ASM_SAD`.*

Across the 12,778 shots that carry `ASM_SAD`, only these three coils separate from
the noise:

| Channel | Shots reading reversed | Shots reading correctly |
| --- | --- | --- |
| M02 | 814 | 4409 |
| M08 | 825 | 4330 |
| M012 | 815 | 4427 |
| Every other coil | 40 or fewer (noise) | about 5250 |

**What we assumed.**

- **The cause is known.** The fault is a fixed sign applied during UDA's analysis
  step, which stayed in place after the wiring was repaired. The raw and analysed
  signals, read independently, show the same boundary.
- **Where the fault starts.** The wiring was repaired somewhere between shots
  24742 and 24783. The analysed data is correct before shot 24782 and reversed
  from 24785, and the shots in between have no usable analysed data, so we apply
  the correction from 24782.
- **The sign is the only thing wrong.** After correction, all three coils agree
  with the eight unaffected coils.

**What we did.** `M02`, `M08` and `M012` are multiplied by −1 for shots
24782–30473. Earlier shots are passed through unchanged, because the analysis flip
was correct for them.

**What this means for you.** The field will not match `ASM_SAD` read from UDA over
shots 24782–30473: expect those three coils to differ by a sign.

### Related UDA signals you should not trust

UDA derives several other signals from these coils using the uncorrected values.
We do not publish them, and they will not be corrected at source. **If you need
any of the following, recompute it from the twelve individual coils in level 2**,
which are corrected:

- `ASM_SAD/D02 2-8`: a difference of two coils that are both reversed, so the
  result is simply negated. Flipping its sign recovers it.
- `ASM_SAD/D05 6-12`: only one coil of the pair is reversed, so from shot 24785
  this channel **adds** the two coils where it should subtract them. No operation
  on the channel alone can recover the difference. Its amplitude relative to a
  single coil jumps from about 0.2 to about 2.1 at that shot.
- `ASM_OUT/SIGNAL`, `THETA`, `THETA_DEVIATION`, `RATING`, `NN_RATING` and
  `NN_PATTERN`: the locked mode detector outputs, computed from the reversed coils.
  Every one of them changes character at shot 24785. The locked mode rating is
  pinned at its maximum on about 71% of shots after that, against 7% before, which
  makes it unusable as either a flag or a measurement.

```{warning}
If you have published or relied on saddle coil results, or on the locked mode
detector, for shots from 24785 onwards, those results are worth re-checking.
```

The link between the reversed coils and the detector outputs is strong but one
step less direct than the coil result itself: the inputs are demonstrably reversed
and every output changes at the same shot, but we cannot rule out from the data
alone that something inside the detector also changed.

## XMB: saddle coil voltage

### Saddle coils M02, M08 and M12 are sign-corrected

| Field | Value |
| --- | --- |
| **UDA signal** | `XMB_SAD/OUT` |
| **Level 2 data** | `magnetics.b_field_tor_probe_saddle_voltage`, channels `M02`, `M08`, `M12` |
| **Shots** | 11708–24781 |
| **Correction** | Multiplied by −1 |
| **Recorded in** | `corrected_channels` attribute |
| **Introduced** | [#157](https://github.com/ukaea/fair-mast-ingestion/pull/157) |

**What was wrong.** The raw voltages are a faithful record of the same three coils
while they were wired backwards, so they read reversed *before* the repair and
correctly after it: the opposite range to the [field](#asm-saddle-coil-field).

**What we assumed.**

- **The cause is known**: the physical wiring reversal, over the same boundary as
  the field.
- **This profile is already processed.** It is published after a background
  subtraction (below), so it is not a copy of the archive. Correcting it puts the
  voltage and the field in the same sign convention.

**What we did.** `M02`, `M08` and `M12` are multiplied by −1 for shots
11708–24781. Later shots are passed through unchanged.

**What this means for you.** The saddle data in level 2 is internally consistent:
all twelve coils, both profiles, every shot, the same sign convention. It will not
match `XMB_SAD` read from UDA over shots 11708–24781: expect those three coils to
differ by a sign.

### Each channel's offset is subtracted

| Field | Value |
| --- | --- |
| **UDA signal** | `XMB_SAD/OUT` |
| **Level 2 data** | `magnetics.b_field_tor_probe_saddle_voltage`, every channel |
| **Shots** | 11708–30473 |
| **Correction** | The mean of the first ten samples is subtracted |
| **Introduced** | [#55](https://github.com/ukaea/fair-mast-ingestion/pull/55) |

**What was wrong.** The raw saddle coil voltages sit on an offset, so a coil does
not read zero when there is no signal.

**What we assumed.**

- **The first ten samples of each channel are recorded before the plasma**, when
  the true signal is zero, so their mean is the channel's offset.
- **The offset is constant through the shot.**

**What we did.** For each channel on each shot, the mean of its first ten samples
is subtracted from the whole trace.

**What this means for you.** The voltages will not match `XMB_SAD` read from UDA:
each channel differs by a constant. A drift in the offset during the shot is not
removed.

## AMC: PF coil currents

### Currents are scaled to the true coil current

| Field | Value |
| --- | --- |
| **UDA signal** | `AMC_SOL CURRENT`, `AMC_P2IL FEED CURRENT` and the other PF coil currents |
| **Level 2 data** | `pf_active.coil_current` |
| **Shots** | All |
| **Correction** | Each channel multiplied by a fixed factor (see [Scale factors](#scale-factors)) |
| **Introduced** | [#110](https://github.com/ukaea/fair-mast-ingestion/pull/110), [#129](https://github.com/ukaea/fair-mast-ingestion/pull/129), [#153](https://github.com/ukaea/fair-mast-ingestion/pull/153) |

**What was wrong.** The archive stores the PF coil feed currents **per turn of the
coil**, and the units it declares for them are wrong. Used as they are, they make
the coil currents too small by the number of turns in each coil, and equilibria
reconstructed from them come out visibly wrong.

The solenoid has a second problem: it is fed through windings connected in
parallel, so its feed current reads twice the current in the coil.

**What we assumed.**

- **The number of turns in each coil**: 12 for P2 inner, 8 for P2 outer and P3, 23
  for P4 and P5, and 4 for P6.
- **The solenoid feed current is twice the coil current**, because of how it is
  wired.

We checked the scaled currents against the PF currents EFIT was given, and by
re-running a free-boundary equilibrium code (FreeGSNKE) on a case that gave a
wrong equilibrium with the unscaled values. It gave a sensible equilibrium once
the scaling was applied.

**What we did.** Each channel is multiplied by the factor in
[Scale factors](#scale-factors).

**What this means for you.** The factors were introduced over three changes, so
files produced at different times can carry different scaling. See
[Release History](release-history.md).

## XMC: Mirnov coils

### Centre column Mirnov coils are scaled to tesla

| Field | Value |
| --- | --- |
| **UDA signal** | `XMC/CC/MT`, `XMC/CC/MV` |
| **Level 2 data** | `magnetics.b_field_tor_probe_cc_field`, `magnetics.b_field_pol_probe_cc_field` |
| **Shots** | All |
| **Correction** | Multiplied by 2×10⁻⁶ |

**What was wrong.** The archive stores these centre column coil signals as raw
voltages, not as a magnetic field.

**What we assumed.** A single factor of 2×10⁻⁶ converts every channel to tesla.
Where this factor comes from is not recorded, and we have not checked it against
data.

**What we did.** Every channel is multiplied by 2×10⁻⁶ and published in tesla.

**What this means for you.** The factor changes only the magnitude of these
signals, not their shape or timing. Treat their absolute magnitude with caution
until the factor is confirmed.

## Known limitations

These are known problems that have not been fixed at the time of writing.

### Empty channels

Some channels are published but contain no data, because the signal could not be
read. **An all-NaN channel means the signal is missing, not that the diagnostic
was off.**

- `magnetics.b_field_tor_probe_saddle_field`, channel `M09`: the archive's
  analysed saddle set has eleven coils, not twelve. There is no `ASM_SAD/M09`.
- `magnetics.b_field_tor_probe_saddle_voltage`, channels `M10`, `M11` and `M12`,
  shots 11708–27619: the archive names these coils `M010`, `M011` and `M012`.

### AMB: flux loops

- **CC04 before shot 25366.** From shot 22372 to 25365 CC04 is intermittently
  dead, on 792 shots. These are published as near-zero noise rather than NaN.
  Check CC04 against its neighbours before using it in this range.
- **Four loops are not published.** The archive holds 19 flux loops in `AMB_FL`,
  but `magnetics.flux_loop_flux` publishes 15. `P2L/1`, `P3L/1`, `P5U/4` and
  `P6U/1` are missing, although EFIT uses all four.
- **The position of P5L/3 looks wrong.** Its stored position (R = 1.7463 m,
  Z = −0.5322 m) does not mirror `P5U/3`, which suggests about R = 1.55 m,
  Z = −0.564 m. The machine description and UDA agree with each other, so the
  error, if it is one, is in the source geometry.

### AYC: Thomson scattering radius

The radius of each Thomson channel (`AYC_R`) changes during a shot by up to
1.8 cm, but level 2 treats it as fixed, using its value at the first time step.
The drift is comparable to the 1 cm spacing of the radial grid.

### ABM: bolometer units

Some MAST signals arrive from UDA without units, so the units on level 2 are
declared by hand in the ingestion mapping. One is unresolved: `bolometer.power` is
declared in W/m², while the IMAS data dictionary types the same quantity in W.

### Data that is not published

- **Halo currents** (`AMH`): the Rogowski coil currents are not published.
- **Mirnov coils** (`XMC`): only a small subset of the arrays is published.
  `b_field_pol_probe_omv_voltage` has 3 channels, `b_field_tor_probe_cc_field` 3
  and `b_field_pol_probe_cc_field` 5.

## Reporting a problem

If you find something that looks wrong in level 2, please open an issue on the
[fair-mast-ingestion repository](https://github.com/ukaea/fair-mast-ingestion/issues).
The most useful report names the signal, the shot range, and what you expected to
see.
