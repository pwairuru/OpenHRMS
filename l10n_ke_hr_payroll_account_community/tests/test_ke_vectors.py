# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Source-slip vector tests (standalone math mirror, no DB required).

How it works: this loader reads every ``tests/vectors/*.json`` file and
replays the shipped rule-body math from
``l10n_ke_hr_payroll_community/data/hr_salary_rule_data.xml``
(KE_NSSF / KE_SHIF / KE_AHL / KE_TAXABLE / KE_PAYE / KE_NET) against the
dated parameters in ``data/ke_rule_parameter_data.xml``. It is a
standalone mirror, NOT a full-payslip run -- the full-payslip oracle
(100k March-2026 + cap/floor/move-sides) lives in
``test_ke_salary_rules.py``, which needs a database. Both must agree;
if this mirror ever disagrees with a Done payslip, the payslip wins
and this mirror must be fixed to match the shipped rule bodies.

Adding a new slip = adding a new JSON file. No code change needed.
Vector JSON schema (all amounts KES, magnitudes, not signs)::

    {"gross": N, "date": "YYYY-MM-DD",
     "pension": N, "mortgage": 0, "post_med": 0,
     "insurance": {"life": N, "health": 0, "edu": 0},
     "disabled": false, "cert": null, "secondary": false,
     "nonresident": false,
     "expected": {"nssf": N, "shif": N, "ahl": N,
                  "taxable": N, "paye": N, "net": N},
     "note": "..."}

ENGINE treatment notes: life/health/edu premiums give a 15% tax
relief credit (capped 5000/month), they are NOT pre-tax deductions;
personal relief is 2400 and applies unless the contract is secondary
or nonresident; nonresidents get no pension/mortgage/post-med
deduction (added back for PAYE) and no reliefs; reported "taxable"
is the resident-basis TAXABLE even for nonresidents. Each expected
value must match within 0.05.
"""
import datetime
import glob
import json
import os
import unittest

VECTOR_DIR = os.path.join(os.path.dirname(__file__), 'vectors')
TOLERANCE = 0.05

PAYE_BANDS = [[24000, 0.10], [8333, 0.25], [467667, 0.30],
              [300000, 0.325], [0, 0.35]]
PERSONAL_RELIEF = 2400.0
INSURANCE_RATE = 0.15
INSURANCE_MAX = 5000.0
PENSION_CAP = 30000.0
MORTGAGE_CAP = 30000.0
POST_MED_CAP = 15000.0
SHIF_RATE = 0.0275
SHIF_MIN = 300.0
AHL_RATE = 0.015
DISABILITY_EXEMPTION = 150000.0
# (date_from, lel, uel, rate) mirrors ke_rule_parameter_data.xml
NSSF_HISTORY = [
    (datetime.date(2026, 2, 1), 9000.0, 108000.0, 0.06),
    (datetime.date(2025, 2, 1), 8000.0, 72000.0, 0.06),
    (datetime.date(2024, 2, 1), 7000.0, 36000.0, 0.06),
]


def _nssf_for(date):
    for date_from, lel, uel, rate in NSSF_HISTORY:
        if date >= date_from:
            return lel, uel, rate
    raise AssertionError('no NSSF params for %s' % date)


def compute(vector):
    """Mirror of the shipped KE rule bodies. Returns signed amounts."""
    gross = float(vector['gross'])
    date = datetime.date.fromisoformat(vector['date'])
    _lel, uel, rate = _nssf_for(date)
    pension = float(vector.get('pension') or 0.0)
    mortgage = float(vector.get('mortgage') or 0.0)
    post_med = float(vector.get('post_med') or 0.0)
    insurance = vector.get('insurance') or {}
    life = float(insurance.get('life') or 0.0)
    health = float(insurance.get('health') or 0.0)
    edu = float(insurance.get('edu') or 0.0)
    disabled = bool(vector.get('disabled'))
    cert = vector.get('cert')
    secondary = bool(vector.get('secondary'))

    nssf = -min(max(min(gross, uel), 0.0) * rate, rate * uel)
    shif = -max(gross * SHIF_RATE, SHIF_MIN)
    ahl = -(gross * AHL_RATE)
    # Pension deduction = min(voluntary + NSSF, monthly cap, 30% of
    # pensionable); v1 pensionable == gross (no allowance rules yet).
    pension_ded = min(pension - nssf, PENSION_CAP, 0.3 * gross)
    taxable = (gross + shif + ahl - pension_ded
               - min(mortgage, MORTGAGE_CAP)
               - min(post_med, POST_MED_CAP))
    pay_taxable = taxable
    if disabled and cert:
        pay_taxable = max(taxable - DISABILITY_EXEMPTION, 0.0)
    nonresident = bool(vector.get('nonresident'))
    if nonresident:
        pay_taxable = (pay_taxable + pension_ded
                       + min(mortgage, MORTGAGE_CAP)
                       + min(post_med, POST_MED_CAP))
    tax = 0.0
    base = 0.0
    for width, band_rate in PAYE_BANDS:
        w = width if width > 0 else float('inf')
        chunk = min(max(pay_taxable - base, 0.0), w)
        tax += chunk * band_rate
        base += w
        if pay_taxable <= base:
            break
    relief = 0.0
    ins_relief = 0.0
    if not secondary and not nonresident:
        relief = PERSONAL_RELIEF
        ins_relief = min(INSURANCE_RATE * (life + health + edu),
                         INSURANCE_MAX)
    paye = -max(tax - relief - ins_relief, 0.0)
    net = gross + nssf + shif + ahl + paye
    return {'nssf': nssf, 'shif': shif, 'ahl': ahl,
            'taxable': taxable, 'paye': paye, 'net': net}


def load_vectors():
    paths = sorted(glob.glob(os.path.join(VECTOR_DIR, '*.json')))
    assert paths, 'no vectors in %s' % VECTOR_DIR
    vectors = []
    for path in paths:
        with open(path, encoding='utf-8') as handle:
            vectors.append((os.path.basename(path), json.load(handle)))
    return vectors


class TestKeVectors(unittest.TestCase):
    def test_vectors(self):
        for name, vector in load_vectors():
            with self.subTest(vector=name):
                got = compute(vector)
                for key, expected in vector['expected'].items():
                    self.assertAlmostEqual(
                        abs(got[key]), float(expected), delta=TOLERANCE,
                        msg='%s: %s got %s expected %s' % (
                            name, key, got[key], expected))


if __name__ == '__main__':
    unittest.main()
