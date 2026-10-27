# Tracking Data Messages (TDM) 10-Point Normative Compliance Matrix

| Rule ID | Check Item | Normative Reference | Verification Method | Pass Criteria |
| :---- | :---- | :---- | :---- | :---- |
| **TDM-001** | CCSDS\_TDM\_VERS Syntax | CCSDS 503.0-B-2 §3.2 | Version String Match | Must equal '1.0' or '2.0' |
| **TDM-002** | Mandatory Header Completeness | CCSDS 503.0-B-2 §3.2 | Field Presence Check | CREATION\_DATE, ORIGINATOR present and non-empty |
| **TDM-003** | Metadata Block Mandatory Keys | CCSDS 503.0-B-2 §3.3 | Entity Validation | TIME\_SYSTEM, START\_TIME, STOP\_TIME, PARTICIPANT\_1, PARTICIPANT\_2, MODE, PATH all present |
| **TDM-004** | Temporal Monotonicity & ISO 8601 | CCSDS 503.0-B-2 §2.4 | Strict ISO Regex & Datetime Parse | \$t\_{k+1} \\ge t\_k\$ and conforms to YYYY-MM-DDThh:mm:ss\[.sss\]Z |
| **TDM-005** | Physical Range Observables Bounds | Radiometric Ranging | Positive Scalar Bounds | RANGE \> 0, round-trip light time \> 0 |
| **TDM-006** | Doppler Shift & Range-Rate Realism | Relativistic Doppler Shift | Physical Kinematic Bounds | Doppler shift corresponds to realistic range-rate \$\|\\dot{\\rho}\| \\le 30.0\$ km/s |
| **TDM-007** | Antenna Pointing Angle Bounds | Ground Station Horizons | Topocentric Domain Validation | \$0^\\circ \\le \\text{Azimuth} \\le 360^\\circ\$, \$0^\\circ \\le \\text{Elevation} \\le 90^\\circ\$ |
| **TDM-008** | RF Band & Transmit Frequency Positivity | ITU / CCSDS 401.0-B | Frequency Domain Check | TRANSMIT\_BAND in {S, X, Ka, Ku...} and carrier frequency \$f\_{tx} \> 0\$ |
| **TDM-009** | Meteorological & Atmospheric Bounds | Tropospheric Refractivity | Terrestrial Boundary Check | \$700 \\le P \\le 1100\$ hPa, \$200 \\le T \\le 350\$ K, \$0 \\le RH \\le 100%\$ |
| **TDM-010** | Strict KVN Line Syntax | CCSDS 503.0-B-2 §6.2 | Lexical Syntax Parser | Strict KEY \= VALUE \[UNIT\] structure without unkeyed drift |

