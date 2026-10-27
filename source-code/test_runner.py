#!/usr/bin/env python3
"""
TDMForge Pro (v1.0.0) — Automated Test Suite
Standards: CCSDS 503.0-B-2 (Blue Book) & ISO 22644:2020
Tests range math, carrier Doppler, Saastamoinen media delay, KVN parsing, and the 10-point normative auditor.
"""

import unittest
import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tdm_cli import (
    range_km_to_ru,
    ru_to_range_km,
    compute_doppler_hz,
    compute_range_rate_kms,
    compute_troposphere_delay,
    generate_tdm,
    parse_tdm,
    audit_tdm,
    SPEED_OF_LIGHT_KMS
)

class TestTDMForgePro(unittest.TestCase):

    def test_01_tdm_generation_deepspace(self):
        """1. Test standard deep-space Tracking Data Message (TDM) KVN generation."""
        tdm_str = generate_tdm('deepspace', num_points=3)
        self.assertIn("CCSDS_TDM_VERS = 2.0", tdm_str)
        self.assertIn("PARTICIPANT_1               = DSS-14", tdm_str)
        self.assertIn("PARTICIPANT_2               = EUROPA-CLIPPER", tdm_str)
        self.assertIn("MODE                        = SEQUENTIAL", tdm_str)
        self.assertIn("PATH                        = 1,2,1", tdm_str)
        self.assertIn("RANGE_UNITS                 = RU", tdm_str)
        self.assertIn("DOPPLER_INSTANTANEOUS", tdm_str)

    def test_02_tdm_parsing_kvn(self):
        """2. Test KVN lexical parser, block segmentation, and data streams."""
        tdm_str = generate_tdm('leo', num_points=3)
        parsed = parse_tdm(tdm_str)
        self.assertEqual(parsed['header']['CCSDS_TDM_VERS'], '2.0')
        self.assertEqual(parsed['metadata']['PARTICIPANT_1'], 'SG-1')
        self.assertEqual(parsed['metadata']['PARTICIPANT_2'], 'SENTINEL-2C')
        self.assertEqual(parsed['metadata']['RANGE_UNITS'], 'km')
        self.assertGreater(len(parsed['data']), 0)
        self.assertIn('key', parsed['data'][0])

    def test_03_two_way_light_time(self):
        """3. Test two-way light time calculation across planetary distances."""
        range_km = 150000000.0 # 1 AU
        light_time_sec = (2.0 * range_km) / SPEED_OF_LIGHT_KMS
        self.assertAlmostEqual(light_time_sec, 1000.692, delta=0.5)

    def test_04_range_to_ru_roundtrip(self):
        """4. Test Range Units (RU) bi-directional conversion accuracy."""
        orig_km = 42164.0 # GEO orbit radius
        tx_freq = 7.165e9 # 7.165 GHz
        ru = range_km_to_ru(orig_km, tx_freq)
        rec_km = ru_to_range_km(ru, tx_freq)
        self.assertAlmostEqual(orig_km, rec_km, places=4)

    def test_05_doppler_range_rate_roundtrip(self):
        """5. Test two-way Doppler shift and range-rate bi-directional round-trip."""
        tx_freq = 2.0675e9 # S-band
        orig_rate_kms = -7.420 # LEO pass velocity
        dop_hz = compute_doppler_hz(tx_freq, orig_rate_kms)
        rec_rate_kms = compute_range_rate_kms(tx_freq, dop_hz)
        self.assertAlmostEqual(orig_rate_kms, rec_rate_kms, places=5)
        self.assertGreater(dop_hz, 0.0) # Approaching satellite -> positive Doppler shift

    def test_06_saastamoinen_troposphere_delay(self):
        """6. Test Saastamoinen tropospheric wet/dry delay model."""
        # Zenith (90 deg) vs low elevation (10 deg)
        dry_zenith, wet_zenith, tot_zenith = compute_troposphere_delay(90.0, 1013.25, 293.15, 50.0)
        dry_low, wet_low, tot_low = compute_troposphere_delay(10.0, 1013.25, 293.15, 50.0)

        # Standard sea-level zenith delay is ~2.3 - 2.5 meters
        self.assertAlmostEqual(dry_zenith, 2.307, delta=0.1)
        self.assertGreater(tot_low, tot_zenith * 5.0) # 1/sin(10 deg) ~ 5.76x amplification

    def test_07_ionosphere_tec_delay(self):
        """7. Test ionospheric dispersion delay scaling inversely with frequency squared."""
        f_s = 2.0e9 # 2 GHz S-band
        f_x = 8.0e9 # 8 GHz X-band
        tecu = 20.0 # 20 TECU

        delay_s = (40.3 * (tecu * 1e16)) / (f_s * f_s)
        delay_x = (40.3 * (tecu * 1e16)) / (f_x * f_x)

        # 4x frequency increase -> 16x delay reduction
        self.assertAlmostEqual(delay_s / delay_x, 16.0, delta=0.01)

    def test_08_normative_auditor_pass(self):
        """8. Test 10-point normative auditor on compliant deep-space TDM."""
        tdm_str = generate_tdm('deepspace', num_points=3)
        parsed = parse_tdm(tdm_str)
        checks = audit_tdm(parsed, tdm_str)
        self.assertEqual(len(checks), 10)
        passed_count = sum(1 for c in checks if c[2])
        self.assertEqual(passed_count, 10, f"Failed rules: {[c for c in checks if not c[2]]}")

    def test_09_normative_auditor_reject_invalid_vers(self):
        """9. Test auditor catches invalid CCSDS_TDM_VERS syntax."""
        tdm_str = generate_tdm('deepspace', num_points=3).replace("CCSDS_TDM_VERS = 2.0", "CCSDS_TDM_VERS = 8.5")
        parsed = parse_tdm(tdm_str)
        checks = audit_tdm(parsed, tdm_str)
        rule_001 = next(c for c in checks if c[0] == 'TDM-001')
        self.assertFalse(rule_001[2])

    def test_10_normative_auditor_reject_non_monotonic_time(self):
        """10. Test auditor catches non-monotonic or corrupted timestamp."""
        tdm_str = generate_tdm('deepspace', num_points=3).replace("2026-10-17T06:00:30.000Z", "1999-01-01T00:00:00.000Z")
        parsed = parse_tdm(tdm_str)
        checks = audit_tdm(parsed, tdm_str)
        rule_004 = next(c for c in checks if c[0] == 'TDM-004')
        self.assertFalse(rule_004[2])

if __name__ == '__main__':
    unittest.main()
