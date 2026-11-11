def migrate(cr, version):
    # Fix ke_fringe_rate 2026 dating: 0.09 was seeded from 2026-01-01, but KRA
    # quarterly rates are 8% Q1-Q3 and 9% Q4. Move the existing 0.09 row to
    # 2026-10-01; the 0.08 Q1-Q3 row is inserted by the updated XML data file
    # (new xmlid, loaded after migrations run).
    cr.execute(
        """
        UPDATE ke_hr_rule_parameter
        SET date_from = DATE '2026-10-01',
            name = 'KE fringe market rate Q4-2026',
            value = '0.09',
            write_date = NOW() AT TIME ZONE 'UTC'
        WHERE code = 'ke_fringe_rate'
          AND date_from = DATE '2026-01-01'
          AND value = '0.09'
        """
    )
