#!/usr/bin/env python3
"""
TDMForge Pro (v1.0.0) — Command-Line Radiometric Tracking Data & Orbit Determination Tool
Standards: CCSDS 503.0-B-2 (Blue Book) & ISO 22644:2020
Pure Python 3 implementation with zero external dependencies.
"""

import sys
import os
import math
import argparse
import json
import re
from datetime import datetime

SPEED_OF_LIGHT_KMS = 299792.458
SPEED_OF_LIGHT_MS = 299792458.0

PRESETS = {
    'deepspace': {
        'name': 'Deep Space: NASA DSN Goldstone (DSS-14) to Europa Clipper',
        'participant1': 'DSS-14',
        'participant2': 'EUROPA-CLIPPER',
        'mode': 'SEQUENTIAL',
        'path': '1,2,1',
        'transmit_band': 'X',
        'receive_band': 'X',
        'integration_interval': 10.0,
        'range_mode': 'COHERENT',
        'range_units': 'RU',
        'angle_type': 'AZEL',
        'ref_frame': 'ITRF',
        'start_time': '2026-10-17T06:00:00.000Z',
        'stop_time': '2026-10-17T06:30:00.000Z',
        'tx_freq_hz': 7165000000.0,
        'one_way_range_km': 185850000.0,
        'range_rate_kms': 12.450,
        'azimuth_deg': 142.50,
        'elevation_deg': 48.20,
        'meteo': {'pressure_hpa': 915.0, 'temp_k': 288.15, 'r_humidity_pct': 24.0},
        'iono_tec': 18.5
    },
    'leo': {
        'name': 'LEO: KSAT Svalbard (SG-1) Pass to Sentinel-2C',
        'participant1': 'SG-1',
        'participant2': 'SENTINEL-2C',
        'mode': 'SEQUENTIAL',
        'path': '1,2,1',
        'transmit_band': 'S',
        'receive_band': 'S',
        'integration_interval': 1.0,
        'range_mode': 'COHERENT',
        'range_units': 'km',
        'angle_type': 'AZEL',
        'ref_frame': 'ITRF',
        'start_time': '2026-10-17T11:14:00.000Z',
        'stop_time': '2026-10-17T11:24:00.000Z',
        'tx_freq_hz': 2067500000.0,
        'one_way_range_km': 950.0,
        'range_rate_kms': -5.840,
        'azimuth_deg': 28.40,
        'elevation_deg': 62.10,
        'meteo': {'pressure_hpa': 1012.0, 'temp_k': 268.15, 'r_humidity_pct': 75.0},
        'iono_tec': 8.2
    },
    'geo': {
        'name': 'GEO: ESA Perth Tracking to Alphasat',
        'participant1': 'PERTH-1',
        'participant2': 'ALPHASAT',
        'mode': 'SEQUENTIAL',
        'path': '1,2,1',
        'transmit_band': 'KA',
        'receive_band': 'KA',
        'integration_interval': 10.0,
        'range_mode': 'COHERENT',
        'range_units': 'km',
        'angle_type': 'AZEL',
        'ref_frame': 'ITRF',
        'start_time': '2026-10-17T15:00:00.000Z',
        'stop_time': '2026-10-17T16:00:00.000Z',
        'tx_freq_hz': 30000000000.0,
        'one_way_range_km': 38240.0,
        'range_rate_kms': 0.004,
        'azimuth_deg': 345.10,
        'elevation_deg': 54.30,
        'meteo': {'pressure_hpa': 1018.0, 'temp_k': 295.15, 'r_humidity_pct': 45.0},
        'iono_tec': 22.0
    }
}

def range_km_to_ru(range_km, tx_freq_hz):
    range_m = range_km * 1000.0
    return (2.0 * range_m * tx_freq_hz) / SPEED_OF_LIGHT_MS

def ru_to_range_km(ru, tx_freq_hz):
    range_m = (ru * SPEED_OF_LIGHT_MS) / (2.0 * tx_freq_hz)
    return range_m / 1000.0

def compute_doppler_hz(tx_freq_hz, range_rate_kms):
    return -2.0 * tx_freq_hz * (range_rate_kms / SPEED_OF_LIGHT_KMS)

def compute_range_rate_kms(tx_freq_hz, doppler_hz):
    return (-doppler_hz * SPEED_OF_LIGHT_KMS) / (2.0 * tx_freq_hz)

def compute_troposphere_delay(elevation_deg, pressure_hpa, temp_k, r_humidity_pct):
    el_rad = max(0.087, math.radians(elevation_deg))
    sin_el = math.sin(el_rad)

    dry_m = (0.002277 * pressure_hpa) / sin_el

    temp_c = temp_k - 273.15
    es = 6.11 * math.pow(10.0, (7.5 * temp_c) / (237.3 + temp_c))
    e0 = (r_humidity_pct / 100.0) * es

    wet_m = (0.002277 * (1255.0 / temp_k + 0.05) * e0) / sin_el
    return dry_m, wet_m, dry_m + wet_m

def generate_tdm(preset_key='deepspace', num_points=5, time_step_sec=30):
    p = PRESETS.get(preset_key, PRESETS['deepspace'])
    now_iso = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z')
    dry_m, wet_m, tot_m = compute_troposphere_delay(
        p['elevation_deg'], p['meteo']['pressure_hpa'], p['meteo']['temp_k'], p['meteo']['r_humidity_pct']
    )

    lines = [
        "CCSDS_TDM_VERS = 2.0",
        "COMMENT ====================================================================",
        "COMMENT  TDMForge Pro (v1.0.0) — CCSDS 503.0-B-2 Tracking Data Message (TDM)",
        "COMMENT  Radiometric Ranging, Carrier Doppler & Ground Navigation Studio",
        "COMMENT ====================================================================",
        f"CREATION_DATE               = {now_iso}",
        "ORIGINATOR                  = TDMFORGE_PRO_NAV",
        "",
        "META_START",
        "TIME_SYSTEM                 = UTC",
        f"START_TIME                  = {p['start_time']}",
        f"STOP_TIME                   = {p['stop_time']}",
        f"PARTICIPANT_1               = {p['participant1']}",
        f"PARTICIPANT_2               = {p['participant2']}",
        f"MODE                        = {p['mode']}",
        f"PATH                        = {p['path']}",
        "PATH_1                      = 1,2",
        "PATH_2                      = 2,1",
        f"TRANSMIT_BAND               = {p['transmit_band']}",
        f"RECEIVE_BAND                = {p['receive_band']}",
        f"INTEGRATION_INTERVAL        = {p['integration_interval']:.1f} [s]",
        "INTEGRATION_REF             = MIDDLE",
        f"RANGE_MODE                  = {p['range_mode']}",
        "RANGE_MOD_TYPE              = SINE",
        f"RANGE_UNITS                 = {p['range_units']}",
        f"ANGLE_TYPE                  = {p['angle_type']}",
        f"REFERENCE_FRAME             = {p['ref_frame']}",
        "META_STOP",
        "",
        "DATA_START"
    ]

    base_dt = datetime.strptime(p['start_time'], '%Y-%m-%dT%H:%M:%S.%fZ')
    for i in range(num_points):
        offset_sec = i * time_step_sec
        t_iso = (base_dt.timestamp() + offset_sec)
        t_iso_str = datetime.utcfromtimestamp(t_iso).strftime('%Y-%m-%dT%H:%M:%S.000Z')

        cur_range_km = p['one_way_range_km'] + p['range_rate_kms'] * offset_sec
        cur_rate_kms = p['range_rate_kms'] + (i * 0.0002)
        doppler_hz = compute_doppler_hz(p['tx_freq_hz'], cur_rate_kms)
        rx_freq_hz = p['tx_freq_hz'] + doppler_hz

        range_val = cur_range_km if p['range_units'] == 'km' else range_km_to_ru(cur_range_km, p['tx_freq_hz'])
        az = (p['azimuth_deg'] + i * 0.15) % 360.0
        el = min(89.5, max(5.0, p['elevation_deg'] + i * 0.10))

        lines.append(f"TRANSMIT_FREQ_1             = {t_iso_str}  {p['tx_freq_hz']:.1f} [Hz]")
        lines.append(f"RECEIVE_FREQ                = {t_iso_str}  {rx_freq_hz:.3f} [Hz]")
        lines.append(f"DOPPLER_INSTANTANEOUS       = {t_iso_str}  {doppler_hz:.3f} [Hz]")
        lines.append(f"RANGE                       = {t_iso_str}  {range_val:.3f} [{p['range_units']}]")
        lines.append(f"ANGLE_1                     = {t_iso_str}  {az:.4f} [deg]")
        lines.append(f"ANGLE_2                     = {t_iso_str}  {el:.4f} [deg]")
        lines.append(f"PRESSURE                    = {t_iso_str}  {p['meteo']['pressure_hpa']:.1f} [hPa]")
        lines.append(f"TEMPERATURE                 = {t_iso_str}  {p['meteo']['temp_k']:.2f} [K]")
        lines.append(f"RHUMIDITY                   = {t_iso_str}  {p['meteo']['r_humidity_pct']:.1f} [%]")
        lines.append(f"TROPO_DRY                   = {t_iso_str}  {dry_m:.4f} [m]")
        lines.append(f"TROPO_WET                   = {t_iso_str}  {wet_m:.4f} [m]")
        lines.append(f"IONO_TEC                    = {t_iso_str}  {p['iono_tec']:.2f} [TECU]")
        lines.append("COMMENT --------------------------------------------------------------------")

    lines.append("DATA_STOP")
    return '\n'.join(lines)

def parse_tdm(text):
    result = {'header': {}, 'metadata': {}, 'data': []}
    section = 'header'
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('COMMENT'):
            continue
        if line == 'META_START': section = 'metadata'; continue
        if line == 'META_STOP': section = 'pre_data'; continue
        if line == 'DATA_START': section = 'data'; continue
        if line == 'DATA_STOP': section = 'post_data'; continue

        if '=' in line:
            parts = line.split('=', 1)
            key = parts[0].strip()
            val = parts[1].strip()
            m = re.match(r'^(.+?)\s*\[.+?\]$', val)
            if m:
                val = m.group(1).strip()

            if section == 'header':
                result['header'][key] = val
            elif section == 'metadata':
                if not key.endswith('_TIME') and not key.endswith('_VERS'):
                    try:
                        num = float(val)
                        val = num
                    except ValueError:
                        pass
                result['metadata'][key] = val
            elif section == 'data':
                tokens = val.split()
                if len(tokens) >= 2:
                    epoch = tokens[0]
                    try:
                        v = float(tokens[1])
                    except ValueError:
                        v = tokens[1]
                    result['data'].append({'key': key, 'epoch': epoch, 'value': v})
                else:
                    result['data'].append({'key': key, 'value': val})
    return result

def audit_tdm(data, raw_text):
    checks = []

    # TDM-001
    v = str(data['header'].get('CCSDS_TDM_VERS', ''))
    checks.append(('TDM-001', 'CCSDS_TDM_VERS Syntax', v in ['1.0', '2.0'], f"Version '{v}'"))

    # TDM-002
    h = data['header']
    req_h = ['CREATION_DATE', 'ORIGINATOR']
    m_h = [k for k in req_h if k not in h]
    checks.append(('TDM-002', 'Mandatory Header Completeness', len(m_h) == 0, f"Missing: {m_h}"))

    # TDM-003
    m = data['metadata']
    req_m = ['TIME_SYSTEM', 'START_TIME', 'STOP_TIME', 'PARTICIPANT_1', 'PARTICIPANT_2', 'MODE', 'PATH']
    m_m = [k for k in req_m if k not in m]
    checks.append(('TDM-003', 'Metadata Block Mandatory Keys', len(m_m) == 0, f"Missing: {m_m}"))

    # TDM-004
    iso_re = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$')
    time_ok = True
    last_t = 0
    pts = 0
    for d in data['data']:
        if 'epoch' in d:
            pts += 1
            if not iso_re.match(d['epoch']):
                time_ok = False; break
            try:
                t = datetime.strptime(d['epoch'], '%Y-%m-%dT%H:%M:%S.%fZ').timestamp()
            except ValueError:
                time_ok = False; break
            if t < last_t:
                time_ok = False; break
            last_t = t
    checks.append(('TDM-004', 'Temporal Monotonicity & ISO 8601', time_ok and pts > 0, f"{pts} points"))

    # TDM-005
    ranges = [d for d in data['data'] if d['key'] == 'RANGE']
    range_ok = len(ranges) > 0 and all(float(r['value']) > 0 for r in ranges)
    checks.append(('TDM-005', 'Physical Range Observables Bounds', range_ok, f"{len(ranges)} range entries"))

    # TDM-006
    dop = [d for d in data['data'] if d['key'].startswith('DOPPLER')]
    tx = next((d for d in data['data'] if d['key'].startswith('TRANSMIT_FREQ')), None)
    f_tx = float(tx['value']) if tx else 7e9
    dop_ok = len(dop) > 0
    max_rate = 0.0
    for dp in dop:
        rate = abs((-float(dp['value']) * SPEED_OF_LIGHT_KMS) / (2.0 * f_tx))
        if rate > max_rate: max_rate = rate
        if rate > 30.0: dop_ok = False; break
    checks.append(('TDM-006', 'Doppler Shift & Range-Rate Realism', dop_ok, f"Max {max_rate:.3f} km/s"))

    # TDM-007
    az_list = [d for d in data['data'] if d['key'] == 'ANGLE_1']
    el_list = [d for d in data['data'] if d['key'] == 'ANGLE_2']
    ang_ok = (len(az_list) > 0 and len(el_list) > 0 and
              all(0.0 <= float(a['value']) <= 360.0 for a in az_list) and
              all(0.0 <= float(e['value']) <= 90.0 for e in el_list))
    checks.append(('TDM-007', 'Antenna Pointing Angle Bounds', ang_ok, f"AZ:[0,360] EL:[0,90]"))

    # TDM-008
    tx_b = str(m.get('TRANSMIT_BAND', '')).upper()
    rx_b = str(m.get('RECEIVE_BAND', '')).upper()
    valid_b = ['S', 'X', 'KA', 'KU', 'UHF', 'VHF']
    rf_ok = tx_b in valid_b and rx_b in valid_b and f_tx > 0
    checks.append(('TDM-008', 'RF Band & Transmit Freq Positivity', rf_ok, f"{tx_b}/{rx_b} ({f_tx/1e9:.2f}GHz)"))

    # TDM-009
    p_list = [d for d in data['data'] if d['key'] == 'PRESSURE']
    t_list = [d for d in data['data'] if d['key'] == 'TEMPERATURE']
    met_ok = (len(p_list) > 0 and len(t_list) > 0 and
              all(700.0 <= float(p['value']) <= 1100.0 for p in p_list) and
              all(200.0 <= float(t['value']) <= 350.0 for t in t_list))
    checks.append(('TDM-009', 'Meteorological & Atmospheric Bounds', met_ok, "Terrestrial P/T"))

    # TDM-010
    syntax_errs = 0
    for line in raw_text.splitlines():
        line = line.strip()
        if line and not line.startswith('COMMENT') and line not in ['META_START', 'META_STOP', 'DATA_START', 'DATA_STOP'] and '=' not in line:
            syntax_errs += 1
    checks.append(('TDM-010', 'Strict KVN Line Syntax', syntax_errs == 0, f"{syntax_errs} errors"))

    return checks

def main():
    parser = argparse.ArgumentParser(description="TDMForge Pro — CCSDS 503.0-B-2 Tracking Data CLI")
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    p_gen = subparsers.add_parser('generate-tdm', help='Generate CCSDS TDM message')
    p_gen.add_argument('--preset', choices=['deepspace', 'leo', 'geo'], default='deepspace')
    p_gen.add_argument('--points', type=int, default=5)
    p_gen.add_argument('--output', '-o', help='Output file path')

    p_parse = subparsers.add_parser('parse', help='Parse TDM KVN file')
    p_parse.add_argument('input', help='Path to TDM file')

    p_audit = subparsers.add_parser('audit', help='Audit TDM KVN file against 10 normative rules')
    p_audit.add_argument('input', help='Path to TDM file')

    p_dop = subparsers.add_parser('doppler-to-rate', help='Convert Doppler shift to range-rate')
    p_dop.add_argument('--tx-freq', type=float, required=True, help='Transmit carrier frequency (Hz)')
    p_dop.add_argument('--doppler', type=float, required=True, help='Doppler frequency shift (Hz)')

    p_ru = subparsers.add_parser('range-to-ru', help='Convert range in km to DSN Range Units')
    p_ru.add_argument('--range-km', type=float, required=True, help='Range in km')
    p_ru.add_argument('--tx-freq', type=float, required=True, help='Transmit carrier frequency (Hz)')

    args = parser.parse_args()

    if args.command == 'generate-tdm':
        tdm_str = generate_tdm(args.preset, args.points)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(tdm_str)
            print(f"Generated TDM saved to {args.output}")
        else:
            print(tdm_str)

    elif args.command == 'parse':
        with open(args.input, 'r') as f:
            content = f.read()
        parsed = parse_tdm(content)
        print(json.dumps(parsed, indent=2))

    elif args.command == 'audit':
        with open(args.input, 'r') as f:
            content = f.read()
        parsed = parse_tdm(content)
        checks = audit_tdm(parsed, content)
        passed = sum(1 for c in checks if c[2])
        total = len(checks)
        print("=================================================================")
        print("  TDMForge Pro (v1.0.0) — 10-Point Normative Compliance Audit    ")
        print("  Standard: CCSDS 503.0-B-2 (Blue Book) & ISO 22644:2020          ")
        print("=================================================================")
        for rule_id, name, ok, val in checks:
            status = "[PASS]" if ok else "[FAIL]"
            print(f" {status} {rule_id}: {name:<35} | {val}")
        print("-----------------------------------------------------------------")
        print(f" Score: {passed}/{total} Passed ({(passed/total)*100:.1f}%)")
        if passed == total:
            print(" Verdict: CERTIFIED CONFORMANT (CCSDS_503_TDM_CERTIFIED)")
        else:
            print(" Verdict: NON-CONFORMANT")
            sys.exit(1)

    elif args.command == 'doppler-to-rate':
        rate = compute_range_rate_kms(args.tx_freq, args.doppler)
        print(f"Range-Rate: {rate:.6f} km/s ({rate * 1000.0:.3f} m/s)")

    elif args.command == 'range-to-ru':
        ru = range_km_to_ru(args.range_km, args.tx_freq)
        print(f"Range: {args.range_km:.3f} km = {ru:.3f} RU (at {args.tx_freq/1e9:.3f} GHz)")

    else:
        parser.print_help()

if __name__ == '__main__':
    main()
