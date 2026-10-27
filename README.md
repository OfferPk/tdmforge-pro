# TDMForge Pro (v1.0.0)

## CCSDS 503.0-B-2 & ISO 22644 Tracking Data Message (TDM) Ground Station & Deep Space Navigation Studio

TDMForge Pro is a commercial-grade, zero-dependency spaceflight navigation and ground station tracking toolkit implementing the international standards **CCSDS 503.0-B-2 (Blue Book)** and **ISO 22644:2020**.

It delivers high-fidelity synthesis, lexical parsing, light-time ranging, carrier Doppler analysis, atmospheric calibration modeling, and normative compliance auditing for standard Tracking Data Messages (TDMs).

---

### Key Capabilities

- **Radiometric Ranging Observables**: Sequential two-way and three-way coherent ranging with round-trip light time (RTLT) and DSN Range Units (RU) calculations.  
- **Carrier Doppler & Range-Rate**: High-precision instantaneous Doppler shift synthesis and relativistic line-of-sight range-rate reconstruction across S, X, and Ka radio frequency bands.  
- **Antenna Pointing Encoders**: Real-time modeling of ground station antenna topocentric horizon tracking angles (Azimuth/Elevation, Right Ascension/Declination, XEYN).  
- **Atmospheric & Media Calibration**: Saastamoinen tropospheric wet/dry refractivity delay engine and ionospheric Total Electron Content (TEC) dispersion delay models.  
- **10-Point Normative Auditor**: Automated compliance verification covering version syntax, mandatory metadata, temporal monotonicity, physical range limits, antenna angle bounds, and strict KVN grammar.  
- **Zero-Dependency Architecture**: Standalone pure JavaScript operations console with interactive polar skyplot rendering and pure Python 3 CLI navigation utility.

---

### Project Structure

tdm-forge-pro/

├── source-code/

│   ├── index.html                   \# Mission Operations Web Console & Polar Skyplot

│   ├── tdm-engine.js                \# Core Radiometric Tracking & Media Calibration Engine

│   ├── tdm-auditor.js               \# 10-Point CCSDS/ISO Normative Compliance Auditor

│   ├── tdm\_cli.py                   \# Python 3 Command-Line Radiometric Navigation Tool

│   ├── tdm-cli.py                   \# CLI Executable Alias

│   └── test\_runner.py               \# Automated Unit Test Suite (10/10 PASS)

├── build/

│   └── tdm-forge-pro-v1.0.0.zip      \# Complete Production Release Package

├── documentation/

│   ├── CCSDS\_TDM\_SPECIFICATION.md   \# Protocol Engineering Guide

│   └── TRACKING\_DATA\_MESSAGE\_COMPLIANCE\_MATRIX.md \# 10-Point Compliance Checklist

├── screenshots/

│   ├── architecture-diagram.svg     \# End-to-End System Architecture

│   └── tdm-studio-preview.svg       \# Mission Console UI & Polar Skyplot Preview

├── README.md                        \# Product Overview & Developer Guide

└── PROGRESS\_REPORT.md               \# Product Factory Cycle Execution Report

---

### Automated Test Suite Execution

python3 source-code/test\_runner.py \-v

Output:

test\_01\_tdm\_generation\_deepspace (\_\_main\_\_.TestTDMForgePro) ... ok

test\_02\_tdm\_parsing\_kvn (\_\_main\_\_.TestTDMForgePro) ... ok

test\_03\_two\_way\_light\_time (\_\_main\_\_.TestTDMForgePro) ... ok

test\_04\_range\_to\_ru\_roundtrip (\_\_main\_\_.TestTDMForgePro) ... ok

test\_05\_doppler\_range\_rate\_roundtrip (\_\_main\_\_.TestTDMForgePro) ... ok

test\_06\_saastamoinen\_troposphere\_delay (\_\_main\_\_.TestTDMForgePro) ... ok

test\_07\_ionosphere\_tec\_delay (\_\_main\_\_.TestTDMForgePro) ... ok

test\_08\_normative\_auditor\_pass (\_\_main\_\_.TestTDMForgePro) ... ok

test\_09\_normative\_auditor\_reject\_invalid\_vers (\_\_main\_\_.TestTDMForgePro) ... ok

test\_10\_normative\_auditor\_reject\_non\_monotonic\_time (\_\_main\_\_.TestTDMForgePro) ... ok

Ran 10 tests in 0.017s

OK

---

### Licensing & Standards Compliance

- Standard: Consultative Committee for Space Data Systems (CCSDS) 503.0-B-2 & ISO 22644:2020.  
- Architecture: Zero-dependency ECMAScript 2022 & Python 3.8+.  
- Commercial License: Dual MIT / Commercial Aerospace Site License (\$2,800/yr).