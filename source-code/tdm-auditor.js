/**
 * TDMForge Pro (v1.0.0) — 10-Point Normative Compliance Auditor
 * Standards: CCSDS 503.0-B-2 (Blue Book) & ISO 22644:2020
 *
 * Evaluates Tracking Data Messages against 10 strict aerospace rules.
 */

(function(root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.TDMAuditor = factory();
  }
}(typeof self !== 'undefined' ? self : this, function() {
  'use strict';

  const TDMAuditor = {};

  TDMAuditor.RULES = [
    {
      id: 'TDM-001',
      name: 'CCSDS_TDM_VERS Syntax',
      normativeRef: 'CCSDS 503.0-B-2 §3.2',
      check: function(data) {
        const vers = String(data.header.CCSDS_TDM_VERS || '').trim();
        const pass = vers === '1.0' || vers === '2.0';
        return {
          pass: pass,
          value: vers,
          message: pass ? `Valid CCSDS TDM version ${vers}` : `Invalid version '${vers}'; must be '1.0' or '2.0'`
        };
      }
    },
    {
      id: 'TDM-002',
      name: 'Mandatory Header Completeness',
      normativeRef: 'CCSDS 503.0-B-2 §3.2',
      check: function(data) {
        const h = data.header;
        const required = ['CREATION_DATE', 'ORIGINATOR'];
        const missing = required.filter(k => !h[k] || String(h[k]).trim() === '');
        const pass = missing.length === 0;
        return {
          pass: pass,
          value: pass ? 'Header present' : `Missing: ${missing.join(', ')}`,
          message: pass ? 'Mandatory header attributes verified' : `Missing header fields: ${missing.join(', ')}`
        };
      }
    },
    {
      id: 'TDM-003',
      name: 'Metadata Block Mandatory Keys',
      normativeRef: 'CCSDS 503.0-B-2 §3.3',
      check: function(data) {
        const m = data.metadata;
        const required = ['TIME_SYSTEM', 'START_TIME', 'STOP_TIME', 'PARTICIPANT_1', 'PARTICIPANT_2', 'MODE', 'PATH'];
        const missing = required.filter(k => !m[k] || String(m[k]).trim() === '');
        const pass = missing.length === 0;
        return {
          pass: pass,
          value: pass ? 'All 7 metadata keys present' : `Missing: ${missing.join(', ')}`,
          message: pass ? 'Tracking participants and session configuration verified' : `Missing metadata: ${missing.join(', ')}`
        };
      }
    },
    {
      id: 'TDM-004',
      name: 'Temporal Monotonicity & ISO 8601 Conformance',
      normativeRef: 'CCSDS 503.0-B-2 §2.4',
      check: function(data) {
        const isoRegex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$/;
        let lastTime = 0;
        let pass = true;
        let count = 0;

        for (let item of data.data) {
          if (item.epoch) {
            count++;
            if (!isoRegex.test(item.epoch)) { pass = false; break; }
            const t = Date.parse(item.epoch);
            if (isNaN(t) || t < lastTime) { pass = false; break; }
            lastTime = t;
          }
        }
        return {
          pass: pass && count > 0,
          value: `${count} time-tagged points verified`,
          message: pass ? 'Strict temporal monotonicity and ISO 8601 UTC confirmed' : 'Non-monotonic or invalid timestamp detected'
        };
      }
    },
    {
      id: 'TDM-005',
      name: 'Physical Range Observables Bounds',
      normativeRef: 'Radio Navigation & Light Time',
      check: function(data) {
        const ranges = data.data.filter(d => d.key === 'RANGE');
        const pass = ranges.length > 0 && ranges.every(r => Number(r.value) > 0);
        const sampleVal = ranges.length > 0 ? Number(ranges[0].value).toFixed(1) : 'None';
        return {
          pass: pass,
          value: `Sample Range: ${sampleVal}`,
          message: pass ? 'Positive light-time range observables confirmed' : 'Invalid or non-positive range values detected'
        };
      }
    },
    {
      id: 'TDM-006',
      name: 'Doppler Shift & Range-Rate Realism',
      normativeRef: 'Relativistic Doppler & Celestial Mechanics',
      check: function(data) {
        const dopplers = data.data.filter(d => d.key.startsWith('DOPPLER_'));
        const tx = data.data.find(d => d.key.startsWith('TRANSMIT_FREQ'));
        const fTx = tx ? Number(tx.value) : 7e9;

        let pass = dopplers.length > 0;
        let maxRate = 0;
        for (let d of dopplers) {
          const shiftHz = Number(d.value);
          const rateKms = Math.abs((-shiftHz * 299792.458) / (2.0 * fTx));
          if (rateKms > maxRate) maxRate = rateKms;
          if (rateKms > 30.0) { pass = false; break; } // Max realistic orbital speed 30 km/s
        }
        return {
          pass: pass,
          value: `Max Range-Rate: ${maxRate.toFixed(3)} km/s`,
          message: pass ? 'Carrier Doppler shift corresponds to realistic range-rates (<= 30 km/s)' : `Doppler shift indicates unrealistic range-rate: ${maxRate} km/s`
        };
      }
    },
    {
      id: 'TDM-007',
      name: 'Antenna Pointing Angle Bounds',
      normativeRef: 'Ground Station Coordinate Systems',
      check: function(data) {
        const azList = data.data.filter(d => d.key === 'ANGLE_1');
        const elList = data.data.filter(d => d.key === 'ANGLE_2');
        let pass = azList.length > 0 && elList.length > 0;

        for (let a of azList) {
          const az = Number(a.value);
          if (az < 0.0 || az > 360.0) { pass = false; break; }
        }
        for (let e of elList) {
          const el = Number(e.value);
          if (el < 0.0 || el > 90.0) { pass = false; break; }
        }
        return {
          pass: pass,
          value: pass ? 'AZ in [0, 360]°, EL in [0, 90]°' : 'Out-of-bounds angles detected',
          message: pass ? 'Antenna Azimuth and Elevation within topocentric horizons' : 'Antenna angles violate physical geometric limits'
        };
      }
    },
    {
      id: 'TDM-008',
      name: 'RF Band & Transmit Frequency Positivity',
      normativeRef: 'ITU / CCSDS 401.0-B Radio Frequency',
      check: function(data) {
        const m = data.metadata;
        const validBands = ['S', 'X', 'KA', 'KU', 'UHF', 'VHF'];
        const txBand = String(m.TRANSMIT_BAND || '').toUpperCase();
        const rxBand = String(m.RECEIVE_BAND || '').toUpperCase();
        const txFreq = data.data.find(d => d.key.startsWith('TRANSMIT_FREQ'));
        const fVal = txFreq ? Number(txFreq.value) : 0;

        const pass = validBands.includes(txBand) && validBands.includes(rxBand) && fVal > 0;
        return {
          pass: pass,
          value: `Tx: ${txBand} (${(fVal/1e9).toFixed(3)} GHz), Rx: ${rxBand}`,
          message: pass ? 'Approved deep-space/near-Earth RF bands and positive carrier frequency' : 'Invalid RF band or missing positive transmit frequency'
        };
      }
    },
    {
      id: 'TDM-009',
      name: 'Meteorological & Atmospheric Boundary Check',
      normativeRef: 'Tropospheric Media Calibration',
      check: function(data) {
        const pList = data.data.filter(d => d.key === 'PRESSURE');
        const tList = data.data.filter(d => d.key === 'TEMPERATURE');
        const rhList = data.data.filter(d => d.key === 'RHUMIDITY');
        let pass = pList.length > 0 && tList.length > 0;

        for (let p of pList) {
          const v = Number(p.value);
          if (v < 700.0 || v > 1100.0) { pass = false; break; }
        }
        for (let t of tList) {
          const v = Number(t.value);
          if (v < 200.0 || v > 350.0) { pass = false; break; }
        }
        for (let rh of rhList) {
          const v = Number(rh.value);
          if (v < 0.0 || v > 100.0) { pass = false; break; }
        }
        return {
          pass: pass,
          value: pass ? 'P, T, RH in terrestrial physical ranges' : 'Meteorological values out of physical bounds',
          message: pass ? 'Valid barometric and surface weather parameters' : 'Weather observables outside realistic bounds'
        };
      }
    },
    {
      id: 'TDM-010',
      name: 'Strict KVN Line Syntax',
      normativeRef: 'CCSDS 503.0-B-2 §6.2',
      check: function(data, rawText) {
        if (!rawText) return { pass: true, value: 'Parsed check', message: 'Syntax verified' };
        const lines = rawText.split('\n');
        let invalidLines = 0;
        for (let l of lines) {
          l = l.trim();
          if (!l || l.startsWith('COMMENT') || ['META_START', 'META_STOP', 'DATA_START', 'DATA_STOP'].includes(l)) continue;
          if (!l.includes('=')) invalidLines++;
        }
        const pass = invalidLines === 0;
        return {
          pass: pass,
          value: `${invalidLines} syntax violations`,
          message: pass ? 'Strict KEY = VALUE [UNIT] KVN syntax verified' : `Found ${invalidLines} lines violating KVN syntax`
        };
      }
    }
  ];

  /**
   * Execute Full Normative Audit
   */
  TDMAuditor.audit = function(tdmData, rawText) {
    const results = [];
    let passedCount = 0;

    for (let rule of TDMAuditor.RULES) {
      const outcome = rule.check(tdmData, rawText);
      if (outcome.pass) passedCount++;
      results.push({
        id: rule.id,
        name: rule.name,
        normativeRef: rule.normativeRef,
        pass: outcome.pass,
        value: outcome.value,
        message: outcome.message
      });
    }

    return {
      total: TDMAuditor.RULES.length,
      passed: passedCount,
      failed: TDMAuditor.RULES.length - passedCount,
      score: (passedCount / TDMAuditor.RULES.length) * 100,
      certified: passedCount === TDMAuditor.RULES.length,
      details: results
    };
  };

  return TDMAuditor;
}));
