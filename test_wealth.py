import unittest
from datetime import date, timedelta
from typing import List
import fund
from fund import Frequency, Fund


class TestFunds(unittest.TestCase):
    def setUp(self) -> None:
        self.fund = Fund()
        self.fund.verbose = False
        self.captured_out = []
        self.fund.print = lambda info: self.captured_out.append(info)

    def test_can_contribute_once_to_fund(self):
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

    def test_change_contribution_frequency(self):
        start_day = date(2023, 1, 1)
        self.fund.contribute(1000, reference_date=start_day, frequency=Frequency.MONTHLY)
        self.fund.advance_time(date(2023, 2, 1))
        self.fund.contribute(1.23, reference_date=date(2023, 2, 1), frequency=Frequency.SEMIMONTHLY)
        self.assertIn("is changing", self.captured_out[0])
        self.fund.advance_time(date(2023, 3, 1))
        self.assertEqual(1002.46, self.fund.get_balance())
        self.fund.contribute(0, frequency=Frequency.NONE)  # turn off contributions
        self.fund.advance_time(date(2030, 12, 31))
        self.assertEqual(1002.46, self.fund.get_balance())  # No change

    def test_annual_percentage_yield(self):
        self.fund.contribute(1000, date(2000, 8, 8))
        self.fund.set_apy(5.0)
        self.fund.advance_time(date(2000, 8, 9))
        balance = self.fund.get_balance()
        self.assertEqual(1000 * (1 + 0.05/365), balance)


if __name__ == '__main__':
    unittest.main()
