# Definitions

A "good" shot is a shot that satisfies the following conditions:

- the time duration of the useful plasma phase (usually, but not necessarily, the flat top) is sufficient for the goals of the experiment, or is cut short by instabilities that are intrinsic to the scenario chosen and thus unavoidable
- the vacuum toroidal magnetic field, the plasma current and the line-averaged density are within 2%, 5% and 25% of the request, respectively
- the auxiliary power from the neutral beam box is within 20% of the request
- all diagnostics and gas delivery systems deemed obligatory for the experiment (in addition to those offered as "standard") are operating in a satisfactory manner, without significant saturation, data loss or other malfunction

A "failed" shot is a shot that does not reach the current flat top as designed, or that is terminated in a unplanned manner in cases with no planned flat top (e.g., in case of a ramp-up disruption study).

## Hard x-rays

Signals:

AHX_HXR_MEZZW means it was on the west mezzanine

AHX_HXR_S: The 'S' refers to south

AHX_HXR_W: The 'W' refers to west

## Notes on Plasma Control System data

XDC signals for target currents: search for “approved” in the signal name and you’ll find the “vetted” version of the coil current targets and dI/dt after the system protection function. These are inputs to the coil current controller. The xdc/pf/f/… signals should include a command for each power supply in units of requested power supply output volts. The xdc/ao/.. signals are the DAC outputs. You should be able to find the coil drive commands again but this time represented in the 0-10V range of the DAC output.
Note that the content of an XDC file can vary depending on the algorithms used, so some shots may not contain the same signals if they weren’t using the standard algorithms (e.g. commissioning and calibration shots)

The XCM signals are recorded plant side. The “vref” or “vset” or “drive” signal should match the xdc/ao signal, i.e. the DAC voltage. The power supply output voltage and current should also be available in XCM, probably in most case with names “volts” and “curr” or “current” but there might be some odd cases of “I” and V” etc.
