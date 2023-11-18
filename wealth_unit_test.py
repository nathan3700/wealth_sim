import unittest
from datetime import date, timedelta

from typing import List

import fund
from fund import Frequency, Fund


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.fund = Fund()

    def test_can_instantiate_fund(self):
        self.assertIsNotNone(self.fund)


    def test_contribution_schedules(self):
        contribution_types: List[fund.BaseContributionSchedule]
        totals = [int(0)] * 3
        start_date = date(1900, 1, 4)
        last_contribution_dates = [start_date] * 3

        def advance_contributions_until(next_date: date):
            for i, c in enumerate(contribution_types):
                totals[i] += c.contribute_until_date(next_date)
                last_contribution_dates[i] = c.last_contribution_date
        cm = fund.MonthlyContributions(1, start_date)
        cbw = fund.BiweeklyContributions(1, start_date)
        csm = fund.SemiMonthlyContributions(1, start_date)
        contribution_types = [cm, cbw, csm]

        self.assertEqual([start_date, start_date, date(1900, 1, 1)], [cm.last_contribution_date, cbw.last_contribution_date, csm.last_contribution_date])
        self.assertEqual([0, 0, 0], totals)  # Nothing contributed yet

        advance_contributions_until(date(1900, 1, 14))  # A just before a semi-monthly
        self.assertEqual([start_date, start_date, date(1900, 1, 1)], last_contribution_dates)
        self.assertEqual([0, 0, 0], totals)  # Nothing contributed yet

        advance_contributions_until(date(1900, 1, 15))  # Semi-monthly is the first to pay
        self.assertEqual([start_date, start_date, date(1900, 1, 15)], last_contribution_dates)
        self.assertEqual([0, 0, 1], totals)

        advance_contributions_until(date(1900, 1, 18))  # First bi-weekly
        self.assertEqual([start_date,  date(1900, 1, 18), date(1900, 1, 15)], last_contribution_dates)
        self.assertEqual([0, 1, 1], totals)

        advance_contributions_until(date(1900, 2, 1))  # Semi-monthly and Bi-weekly both hit on Feb 1
        self.assertEqual([start_date,  date(1900, 2, 1), date(1900, 2, 1)], last_contribution_dates)
        self.assertEqual([0, 2, 2], totals)

        advance_contributions_until(date(1900, 2, 4))  # First monthly comes in
        self.assertEqual([date(1900, 2, 4),  date(1900, 2, 1), date(1900, 2, 1)], last_contribution_dates)
        self.assertEqual([1, 2, 2], totals)

        advance_contributions_until(date(1901, 2, 4))  # 1 year later
        self.assertEqual([date(1901, 2, 4),  date(1901, 2, 1), date(1901, 2, 1)], last_contribution_dates)
        self.assertEqual([1 + 12, 2 + 52/2, 2 + 24], totals)


    def test_can_contribute_to_fund(self):
        self.fund.contribute(10_000.00)
        balance = self.fund.get_balance()
        self.assertEqual(balance, 10_000)

    def test_can_contribute_monthly(self):
        start_day = date(2023, 10, 1)
        self.fund.contribute(1000, reference_date=start_day, frequency=Frequency.MONTHLY)
        self.fund.advance_time(date(2023, 12, 1))
        balance = self.fund.get_balance()
        self.assertEqual(balance, 2000)

    def test_can_contribute_biweekly(self):
        start_day = date(2023, 10, 1)
        self.fund.contribute(1000, reference_date=start_day, frequency=Frequency.BIWEEKLY)
        self.fund.advance_time(start_day + timedelta(days=6, weeks=3))
        balance = self.fund.get_balance()
        self.assertEqual(balance, 1000)
        self.fund.advance_time(start_day + timedelta(weeks=4))
        self.assertEqual(2000, self.fund.get_balance())


if __name__ == '__main__':
    unittest.main()
