/**
 * TDMForge Pro (v1.0.0) — Core Radiometric Tracking & Navigation Engine
 * Standards: CCSDS 503.0-B-2 (Blue Book) & ISO 22644:2020
 *
 * Implements:
 * - Two-way coherent range observables & Range Unit (RU) conversions
 * - Carrier Doppler shift & range-rate synthesis (One-way, Two-way, Three-way)
 * - Ground antenna pointing tracking angles (AZEL, RADEC, XEYN)
 * - Atmospheric media corrections: Saastamoinen tropospheric wet/dry delay & ionospheric TEC
 * - CCSDS Tracking Data Message (TDM) KVN serializer & lexical parser
 */

(function(root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.TDMEngine = factory();
  }
}(typeof self !== 'undefined' ? self : this, function() {
  'use strict';

  const TDMEngine = {};

  // Standard Physical & Astrodynamic Constants
  TDMEngine.SPEED_OF_LIGHT_KMS = 299792.458; // km/s
  TDMEngine.SPEED_OF_LIGHT_MS = 299792458.0; // m/s

  // Transponder Turnaround Ratios (CCSDS 401.0-B)
  TDMEngine.TURNAROUND_RATIOS = {
    'X_BAND': 880.0 / 749.0, // ~1.1748998
    'S_BAND': 240.0 / 221.0, // ~1.0859728
    'KA_BAND': 3344.0 / 3599.0 // ~0.9291469
  };

  /**
   * Mission Operations Presets
   */
  TDMEngine.PRESETS = {
    DEEP_SPACE_DSN: {
      name: 'Deep Space: NASA DSN Goldstone (DSS-14) to Europa Clipper',
      participant1: 'DSS-14',
      participant2: 'EUROPA-CLIPPER',
      mode: 'SEQUENTIAL',
      path: '1,2,1',
      transmitBand: 'X',
      receiveBand: 'X',
      integrationInterval: 10.0,
      rangeMode: 'COHERENT',
      rangeUnits: 'RU',
      angleType: 'AZEL',
      refFrame: 'ITRF',
      startTime: '2026-10-17T06:00:00.000Z',
      stopTime: '2026-10-17T06:30:00.000Z',
      txFreqHz: 7165000000.0, // 7.165 GHz (X-band uplink)
      oneWayRangeKm: 185850000.0, // ~1.24 AU
      rangeRateKms: 12.450, // Recession velocity
      azimuthDeg: 142.50,
      elevationDeg: 48.20,
      meteo: { pressureHpa: 915.0, tempK: 288.15, rHumidityPct: 24.0 },
      ionoTEC: 18.5 // TECU
    },
    LEO_PASS_KSAT: {
      name: 'LEO: KSAT Svalbard (SG-1) Pass to Sentinel-2C',
      participant1: 'SG-1',
      participant2: 'SENTINEL-2C',
      mode: 'SEQUENTIAL',
      path: '1,2,1',
      transmitBand: 'S',
      receiveBand: 'S',
      integrationInterval: 1.0,
      rangeMode: 'COHERENT',
      rangeUnits: 'km',
      angleType: 'AZEL',
      refFrame: 'ITRF',
      startTime: '2026-10-17T11:14:00.000Z',
      stopTime: '2026-10-17T11:24:00.000Z',
      txFreqHz: 2067500000.0, // 2.0675 GHz (S-band uplink)
      oneWayRangeKm: 950.0,
      rangeRateKms: -5.840, // High approach velocity
      azimuthDeg: 28.40,
      elevationDeg: 62.10,
      meteo: { pressureHpa: 1012.0, tempK: 268.15, rHumidityPct: 75.0 },
      ionoTEC: 8.2
    },
    GEO_STATIONARY: {
      name: 'GEO: ESA Perth Tracking to Alphasat In-Orbit Verification',
      participant1: 'PERTH-1',
      participant2: 'ALPHASAT',
      mode: 'SEQUENTIAL',
      path: '1,2,1',
      transmitBand: 'KA',
      receiveBand: 'KA',
      integrationInterval: 10.0,
      rangeMode: 'COHERENT',
      rangeUnits: 'km',
      angleType: 'AZEL',
      refFrame: 'ITRF',
      startTime: '2026-10-17T15:00:00.000Z',
      stopTime: '2026-10-17T16:00:00.000Z',
      txFreqHz: 30000000000.0, // 30 GHz Ka-band
      oneWayRangeKm: 38240.0,
      rangeRateKms: 0.004, // Residual drift
      azimuthDeg: 345.10,
      elevationDeg: 54.30,
      meteo: { pressureHpa: 1018.0, tempK: 295.15, rHumidityPct: 45.0 },
      ionoTEC: 22.0
    }
  };

  /**
   * Two-Way Light Time & Range Unit (RU) Calculations
   */
  TDMEngine.computeTwoWayLightTime = function(rangeKm) {
    return (2.0 * rangeKm) / TDMEngine.SPEED_OF_LIGHT_KMS; // seconds
  };

  TDMEngine.rangeKmToRU = function(rangeKm, txFreqHz) {
    // Standard DSN RU definition: 1 RU corresponds to phase delay of carrier cycle
    // In deep space DSN: RU = 2 * range_m * (txFreqHz / c)
    const rangeM = rangeKm * 1000.0;
    return (2.0 * rangeM * txFreqHz) / TDMEngine.SPEED_OF_LIGHT_MS;
  };

  TDMEngine.ruToRangeKm = function(ru, txFreqHz) {
    const rangeM = (ru * TDMEngine.SPEED_OF_LIGHT_MS) / (2.0 * txFreqHz);
    return rangeM / 1000.0;
  };

  /**
   * Two-Way Carrier Doppler Shift & Range Rate Synthesis
   * Delta_f = -2 * f_tx * (rangeRate / c)
   */
  TDMEngine.computeDopplerShiftHz = function(txFreqHz, rangeRateKms) {
    return -2.0 * txFreqHz * (rangeRateKms / TDMEngine.SPEED_OF_LIGHT_KMS);
  };

  TDMEngine.computeRangeRateFromDoppler = function(txFreqHz, dopplerShiftHz) {
    return (-dopplerShiftHz * TDMEngine.SPEED_OF_LIGHT_KMS) / (2.0 * txFreqHz);
  };

  /**
   * Atmospheric Media Delay Models
   */
  TDMEngine.computeSaastamoinenTroposphereDelay = function(elevationDeg, pressureHpa, tempK, rHumidityPct) {
    const elRad = Math.max(0.087, (elevationDeg * Math.PI) / 180.0); // Clamp to 5 deg minimum to avoid horizon singularities
    const sinEl = Math.sin(elRad);

    // Dry hydrostatic component (Saastamoinen 1972)
    const dryDelayM = (0.002277 * pressureHpa) / sinEl;

    // Water vapor partial pressure e0 (hPa) via Tetens equation
    const tempC = tempK - 273.15;
    const es = 6.11 * Math.pow(10, (7.5 * tempC) / (237.3 + tempC));
    const e0 = (rHumidityPct / 100.0) * es;

    // Wet component
    const wetDelayM = (0.002277 * (1255.0 / tempK + 0.05) * e0) / sinEl;

    return {
      dryDelayM: dryDelayM,
      wetDelayM: wetDelayM,
      totalDelayM: dryDelayM + wetDelayM
    };
  };

  TDMEngine.computeIonosphereDelay = function(txFreqHz, tecu) {
    // Delta_rho = 40.3 * TEC / f^2
    // 1 TECU = 1e16 electrons / m^2
    const tecEl = tecu * 1e16;
    const delayM = (40.3 * tecEl) / (txFreqHz * txFreqHz);
    return delayM;
  };

  /**
   * Generate Full CCSDS 503.0-B-2 Tracking Data Message (KVN Format)
   */
  TDMEngine.generateTDMKVN = function(config, numPoints = 5, timeStepSec = 30) {
    const p = config || TDMEngine.PRESETS.DEEP_SPACE_DSN;
    const nowISO = new Date().toISOString();
    const tropo = TDMEngine.computeSaastamoinenTroposphereDelay(
      p.elevationDeg,
      p.meteo.pressureHpa,
      p.meteo.tempK,
      p.meteo.rHumidityPct
    );
    const ionoDelayM = TDMEngine.computeIonosphereDelay(p.txFreqHz, p.ionoTEC);

    const lines = [
      'CCSDS_TDM_VERS = 2.0',
      'COMMENT ====================================================================',
      'COMMENT  TDMForge Pro (v1.0.0) — CCSDS 503.0-B-2 / ISO 22644 Tracking Data Message',
      'COMMENT  Radiometric Ranging, Carrier Doppler & Ground Navigation Studio',
      'COMMENT ====================================================================',
      `CREATION_DATE               = ${nowISO}`,
      'ORIGINATOR                  = TDMFORGE_PRO_NAV',
      '',
      'META_START',
      'TIME_SYSTEM                 = UTC',
      `START_TIME                  = ${p.startTime}`,
      `STOP_TIME                   = ${p.stopTime}`,
      `PARTICIPANT_1               = ${p.participant1}`,
      `PARTICIPANT_2               = ${p.participant2}`,
      `MODE                        = ${p.mode}`,
      `PATH                        = ${p.path}`,
      'PATH_1                      = 1,2',
      'PATH_2                      = 2,1',
      `TRANSMIT_BAND               = ${p.transmitBand}`,
      `RECEIVE_BAND                = ${p.receiveBand}`,
      `INTEGRATION_INTERVAL        = ${p.integrationInterval.toFixed(1)} [s]`,
      'INTEGRATION_REF             = MIDDLE',
      `RANGE_MODE                  = ${p.rangeMode}`,
      'RANGE_MOD_TYPE              = SINE',
      `RANGE_UNITS                 = ${p.rangeUnits}`,
      `ANGLE_TYPE                  = ${p.angleType}`,
      `REFERENCE_FRAME             = ${p.refFrame}`,
      'META_STOP',
      '',
      'DATA_START'
    ];

    const baseTimeMs = new Date(p.startTime).getTime();
    for (let i = 0; i < numPoints; i++) {
      const tMs = baseTimeMs + i * timeStepSec * 1000;
      const tISO = new Date(tMs).toISOString();

      // Slightly perturb range and range-rate along track
      const currentRangeKm = p.oneWayRangeKm + (p.rangeRateKms * (i * timeStepSec));
      const currentRateKms = p.rangeRateKms + (i * 0.0002);
      const dopplerHz = TDMEngine.computeDopplerShiftHz(p.txFreqHz, currentRateKms);
      const rxFreqHz = p.txFreqHz + dopplerHz;

      let rangeVal = currentRangeKm;
      if (p.rangeUnits === 'RU') {
        rangeVal = TDMEngine.rangeKmToRU(currentRangeKm, p.txFreqHz);
      }

      const az = (p.azimuthDeg + i * 0.15) % 360.0;
      const el = Math.min(89.5, Math.max(5.0, p.elevationDeg + i * 0.10));

      lines.push(`TRANSMIT_FREQ_1             = ${tISO}  ${p.txFreqHz.toFixed(1)} [Hz]`);
      lines.push(`RECEIVE_FREQ                = ${tISO}  ${rxFreqHz.toFixed(3)} [Hz]`);
      lines.push(`DOPPLER_INSTANTANEOUS       = ${tISO}  ${dopplerHz.toFixed(3)} [Hz]`);
      lines.push(`RANGE                       = ${tISO}  ${rangeVal.toFixed(3)} [${p.rangeUnits}]`);
      lines.push(`ANGLE_1                     = ${tISO}  ${az.toFixed(4)} [deg]`);
      lines.push(`ANGLE_2                     = ${tISO}  ${el.toFixed(4)} [deg]`);
      lines.push(`PRESSURE                    = ${tISO}  ${p.meteo.pressureHpa.toFixed(1)} [hPa]`);
      lines.push(`TEMPERATURE                 = ${tISO}  ${p.meteo.tempK.toFixed(2)} [K]`);
      lines.push(`RHUMIDITY                   = ${tISO}  ${p.meteo.rHumidityPct.toFixed(1)} [%]`);
      lines.push(`TROPO_DRY                   = ${tISO}  ${tropo.dryDelayM.toFixed(4)} [m]`);
      lines.push(`TROPO_WET                   = ${tISO}  ${tropo.wetDelayM.toFixed(4)} [m]`);
      lines.push(`IONO_TEC                    = ${tISO}  ${p.ionoTEC.toFixed(2)} [TECU]`);
      lines.push('COMMENT --------------------------------------------------------------------');
    }

    lines.push('DATA_STOP');
    return lines.join('\n');
  };

  /**
   * Parse KVN TDM Text into Structured Object
   */
  TDMEngine.parseTDMKVN = function(text) {
    const result = {
      header: {},
      metadata: {},
      data: [],
      comments: []
    };

    let section = 'header';
    const lines = text.split('\n');

    for (let line of lines) {
      line = line.trim();
      if (!line) continue;
      if (line.startsWith('COMMENT')) {
        result.comments.push(line.replace(/^COMMENT\s*/, ''));
        continue;
      }

      if (line === 'META_START') { section = 'metadata'; continue; }
      if (line === 'META_STOP') { section = 'pre_data'; continue; }
      if (line === 'DATA_START') { section = 'data'; continue; }
      if (line === 'DATA_STOP') { section = 'post_data'; continue; }

      if (line.includes('=')) {
        const parts = line.split('=');
        const key = parts[0].trim();
        let val = parts.slice(1).join('=').trim();
        const m = val.match(/^(.+?)\s*\[.+?\]$/);
        if (m) val = m[1].trim();

        if (section === 'header') {
          result.header[key] = val;
        } else if (section === 'metadata') {
          const num = Number(val);
          result.metadata[key] = (!isNaN(num) && val !== '' && !key.endsWith('_TIME')) ? num : val;
        } else if (section === 'data') {
          // Data line format: KEY = EPOCH VALUE
          const tokens = val.split(/\s+/);
          if (tokens.length >= 2) {
            const epoch = tokens[0];
            const numVal = Number(tokens[1]);
            result.data.push({
              key: key,
              epoch: epoch,
              value: !isNaN(numVal) ? numVal : tokens[1]
            });
          } else {
            result.data.push({ key: key, value: val });
          }
        }
      }
    }

    return result;
  };

  return TDMEngine;
}));
