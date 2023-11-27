import unittest
from datetime import date, timedelta
from typing import List
import fund
from fund import Frequency, Fund


class TestFunds(unittest.TestCase):
    def setUp(self) -> None:
        self.fund = Fund(date(1900, 1, 1), "Unit Test Fund")
        self.fund.verbose = False
        self.captured_out = []
        self.fund.print = lambda info: self.captured_out.append(info)

    def test_can_contribute_once_to_fund(self):
        self.fund.contribute(10_000.00, self.fund.get_current_date() + timedelta(days=1))
        self.assertEqual(0, self.fund.get_balance())
        self.fund.advance_time(self.fund.get_current_date() + timedelta(days=1))
        self.assertEqual(10_000, self.fund.get_balance())
        self.fund.contribute(10_000.00, self.fund.get_current_date() + timedelta(days=1))
        self.fund.contribute(10_000.00, self.fund.get_current_date() + timedelta(days=2))
        self.fund.advance_time(self.fund.get_current_date() + timedelta(days=2))
        self.assertEqual(30_000, self.fund.get_balance())

    def test_can_contribute_monthly(self):
        start_day = date(2023, 10, 1)
        self.fund.contribute(1000, start_date=start_day, frequency=Frequency.MONTHLY)
        self.fund.advance_time(date(2023, 12, 1))
        balance = self.fund.get_balance()
        self.assertEqual(balance, 3000)

    def test_can_contribute_biweekly(self):
        start_day = date(2023, 10, 1)
        self.fund.contribute(1000, start_date=start_day, frequency=Frequency.BIWEEKLY)
        self.fund.advance_time(start_day + timedelta(days=6, weeks=3))
        balance = self.fund.get_balance()
        self.assertEqual(balance, 2000)
        self.fund.advance_time(start_day + timedelta(weeks=4))
        self.assertEqual(3000, self.fund.get_balance())

    def test_change_contribution_frequency(self):
        start_day = date(2023, 1, 1)
        self.fund.contribute(1000, start_date=start_day, frequency=Frequency.MONTHLY)
        self.fund.advance_time(date(2023, 1, 2))
        self.fund.contribute(1.23, start_date=date(2023, 1, 15), frequency=Frequency.SEMIMONTHLY)
        self.assertIn("is changing", self.captured_out[0])
        self.fund.advance_time(date(2023, 2, 1))
        self.assertEqual(1002.46, self.fund.get_balance())
        self.fund.contribute(0, date(2023, 2, 2), frequency=Frequency.NONE)  # turn off history
        self.fund.advance_time(date(2030, 12, 31))
        self.assertEqual(1002.46, self.fund.get_balance())  # No change

    def test_set_apy(self):
        apy = 5.0
        self.fund.set_apy(apy)
        simple_daily_rate = apy/(365 * 100)
        annual_rate_with_simple_daily_rate = (1 + apy/36500) ** 365 - 1
        correction_factor = (apy/100) / annual_rate_with_simple_daily_rate
        effective_daily_rate = simple_daily_rate * correction_factor
        self.assertEqual(effective_daily_rate, self.fund.daily_rate)

        # Now Test going the other way, if we set the daily_rate, it should update APY
        self.fund.set_daily_rate(simple_daily_rate)
        self.assertEqual(annual_rate_with_simple_daily_rate, self.fund.apy)

    def test_annual_percentage_yield(self):
        self.fund.advance_time(date(2000, 8, 7))
        self.fund.contribute(1000, date(2000, 8, 8))
        self.fund.advance_time(date(2000, 8, 8))
        apy = 5.0
        self.fund.set_apy(apy)
        effective_daily_rate = self.fund.daily_rate

        self.fund.advance_time(date(2000, 8, 9))
        balance = self.fund.get_balance()
        self.assertEqual(1000 * (1 + effective_daily_rate), balance)
        self.fund.advance_time((date(2001, 8, 8)))
        elapsed_days = (date(2001, 8, 8) - date(2000, 8, 8)).days
        self.assertEqual(365, elapsed_days)
        self.assertEqual(1000 * (1 + effective_daily_rate) ** elapsed_days, self.fund.get_balance())

        self.fund = Fund(date(1899, 12, 31), "Large Fund")
        self.fund.contribute(1_000_000, date(1900, 1, 1))
        self.fund.advance_time(date(1900, 1, 1))
        self.fund.set_apy(5.0)
        self.fund.advance_time(date(2000, 1, 1))
        elapsed_days = (date(2000, 1, 1) - date(1900, 1, 1)).days
        self.assertEqual((1000000 * (1 + self.fund.daily_rate) ** elapsed_days), self.fund.get_balance())

    def test_apply_interest_only_after_contributions(self):
        self.fund.set_daily_rate(.01)
        self.fund.contribute(1.00, date(1978, 6, 1), frequency=Frequency.SEMIMONTHLY)
        self.fund.advance_time(date(1978, 6, 15))
        self.assertEqual(1 * (1.01 ** 14) + 1, self.fund.get_balance())  # 14 days of growth on $1 and another $1
        balance = self.fund.get_balance()
        self.fund.advance_time(date(1978, 7, 15))
        # Accrue interest 16 days until July 1st, add $1, accrue 14 more days, add $1
        self.assertEqual((balance * (1.01 ** 16) + 1) * (1.01 ** 14) + 1, self.fund.get_balance())


if __name__ == '__main__':
    unittest.main()
