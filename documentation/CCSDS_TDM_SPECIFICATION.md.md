# CCSDS 503.0-B-2 & ISO 22644 Tracking Data Message (TDM) Technical Specification

## 1\. Executive Summary & Normative Scope

The Consultative Committee for Space Data Systems (CCSDS) 503.0-B-2 Blue Book and ISO 22644:2020 standard define standardized data formats for exchanging radiometric tracking data between ground tracking stations (such as NASA DSN, ESA ESTRACK, KSAT, SSC) and satellite flight dynamics facilities.

Radiometric observables recorded in TDMs form the observational foundation for Spacecraft Orbit Determination (OD), deep space radio science, gravity field mapping, and ground antenna calibration.

---

## 2\. Radiometric Tracking Observables Architecture

### 2.1 Range Observables

Range measurements determine the light-time distance between the ground station antenna (`PARTICIPANT_1`) and the target spacecraft (`PARTICIPANT_2`):

- **Sequential Two-Way Ranging (`MODE = SEQUENTIAL`, `PATH = 1,2,1`)**: An uplink carrier modulated by ranging tones or pseudo-random noise (PN) codes is transmitted by the ground station, transponded coherently by the spacecraft transponder, and received back at the station.  
- **Round-Trip Light Time (RTLT)**: \$\$\\tau \= t\_{\\text{receive}} \- t\_{\\text{transmit}} \= \\frac{2 \\rho}{c}\$\$  
- **Range Units (RU)**: In deep-space tracking (NASA DSN), range is expressed in dimensionless Range Units (RU): \$\$\\text{RU} \= \\frac{2 \\rho \\cdot f\_{tx}}{c}\$\$

### 2.2 Carrier Doppler Shift & Range-Rate

Coherent transponding preserves the frequency phase relationship between uplink and downlink via the transponder turnaround ratio \$k\$ (e.g. \$k \= 880/749\$ for X-band). The two-way carrier Doppler shift \$\\Delta f\$ directly measures relative line-of-sight range-rate \$\\dot{\\rho}\$: \$\$\\Delta f \= \-2 f\_{tx} \\left( \\frac{\\dot{\\rho}}{c} \\right) \\implies \\dot{\\rho} \= \-\\frac{c \\cdot \\Delta f}{2 f\_{tx}}\$\$

### 2.3 Antenna Pointing Angles

- **AZEL**: Topocentric Azimuth (\$0^\\circ \\le \\text{Az} \\le 360^\\circ\$ clockwise from True North) and Elevation (\$0^\\circ \\le \\text{El} \\le 90^\\circ\$ above the local horizon).  
- **RADEC**: Topocentric Right Ascension (\$\\alpha\$) and Declination (\$\\delta\$) in celestial inertial coordinates.  
- **XEYN**: X-East / Y-North angles for cross-elevation mount tracking antennas.

---

## 3\. Atmospheric & Media Calibration Models

### 3.1 Saastamoinen Troposphere Delay Model

Atmospheric refractivity introduces excess propagation path delay modeled by Saastamoinen (1972): \$\$\\Delta \\rho\_{dry} \= \\frac{0.002277 \\cdot P\_0}{\\sin(\\text{El})}, \\quad \\Delta \\rho\_{wet} \= \\frac{0.002277}{\\sin(\\text{El})} \\left(\\frac{1255}{T\_0} \+ 0.05\\right) e\_0\$\$ where \$P\_0\$ is surface pressure (hPa), \$T\_0\$ is temperature (K), and \$e\_0\$ is water vapor pressure (hPa).

### 3.2 Ionospheric Dispersive Group Delay

Free electrons in the ionosphere cause a frequency-dependent group delay proportional to the Total Electron Content (TEC): \$\$\\Delta \\rho\_{iono} \= \\frac{40.3 \\cdot \\text{TEC}}{f\_{tx}^2} \\text{ \[meters\]}\$\$ where \$1\\text{ TECU} \= 10^{16}\\text{ electrons/m}^2\$.

---

## 4\. Normative KVN Tracking Data Message (TDM) Structure

CCSDS\_TDM\_VERS \= 2.0

CREATION\_DATE               \= 2026-10-17T06:00:00.000Z

ORIGINATOR                  \= TDMFORGE\_PRO\_NAV

META\_START

TIME\_SYSTEM                 \= UTC

START\_TIME                  \= 2026-10-17T06:00:00.000Z

STOP\_TIME                   \= 2026-10-17T06:30:00.000Z

PARTICIPANT\_1               \= DSS-14

PARTICIPANT\_2               \= EUROPA-CLIPPER

MODE                        \= SEQUENTIAL

PATH                        \= 1,2,1

PATH\_1                      \= 1,2

PATH\_2                      \= 2,1

TRANSMIT\_BAND               \= X

RECEIVE\_BAND                \= X

INTEGRATION\_INTERVAL        \= 10.0 \[s\]

INTEGRATION\_REF             \= MIDDLE

RANGE\_MODE                  \= COHERENT

RANGE\_MOD\_TYPE              \= SINE

RANGE\_UNITS                 \= RU

ANGLE\_TYPE                  \= AZEL

REFERENCE\_FRAME             \= ITRF

META\_STOP

DATA\_START

TRANSMIT\_FREQ\_1             \= 2026-10-17T06:00:00.000Z  7165000000.0 \[Hz\]

RECEIVE\_FREQ                \= 2026-10-17T06:00:00.000Z  7164404960.000 \[Hz\]

DOPPLER\_INSTANTANEOUS       \= 2026-10-17T06:00:00.000Z  \-595040.000 \[Hz\]

RANGE                       \= 2026-10-17T06:00:00.000Z  8883652875143.000 \[RU\]

ANGLE\_1                     \= 2026-10-17T06:00:00.000Z  142.5000 \[deg\]

ANGLE\_2                     \= 2026-10-17T06:00:00.000Z  48.2000 \[deg\]

PRESSURE                    \= 2026-10-17T06:00:00.000Z  915.0 \[hPa\]

TEMPERATURE                 \= 2026-10-17T06:00:00.000Z  288.15 \[K\]

RHUMIDITY                   \= 2026-10-17T06:00:00.000Z  24.0 \[%\]

TROPO\_DRY                   \= 2026-10-17T06:00:00.000Z  2.7981 \[m\]

TROPO\_WET                   \= 2026-10-17T06:00:00.000Z  0.0384 \[m\]

IONO\_TEC                    \= 2026-10-17T06:00:00.000Z  18.50 \[TECU\]

DATA\_STOP