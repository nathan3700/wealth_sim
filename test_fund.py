import unittest
from datetime import date, timedelta
import math
from wealth_fund import Frequency, Fund
from fund_transaction import FundTransactionType


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
        self.assertEqual(3000, self.fund.total_contributions)  # Check total contrib variable

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
        periodic_changes = [c for c in self.fund.history if c.type == FundTransactionType.PERIODIC_CHANGE]
        self.assertEqual(2, len(periodic_changes))
        self.fund.advance_time(date(2023, 2, 1))
        self.assertEqual(1002.46, self.fund.get_balance())
        self.fund.contribute(0, date(2023, 2, 2), frequency=Frequency.NONE)  # turn off history
        self.fund.advance_time(date(2030, 12, 31))
        self.assertEqual(1002.46, self.fund.get_balance())  # No change

    def test_set_apy(self):
        apy = 5.0
        self.fund.set_apy(apy)
        effective_daily_rate = math.exp(math.log((apy/100)+1)/365) - 1
        self.assertEqual(effective_daily_rate, self.fund.daily_rate)

        # Now Test going the other way, if we set the daily_rate, it should update APY
        self.fund.set_daily_rate(effective_daily_rate)
        self.assertEqual(5, self.fund.apy)

    def test_annual_percentage_yield(self):
        self.fund.advance_time(date(2000, 8, 7))
        self.fund.contribute(1000, date(2000, 8, 8))
        self.fund.advance_time(date(2000, 8, 8))
        apy = 5.0
        self.fund.set_apy(apy)
        effective_daily_rate = self.fund.daily_rate

        self.fund.advance_time(date(2000, 8, 9))
        balance = self.fund.get_balance()
        self.assertEqual(self.fund.nearest_hundredth(1000 * (1 + effective_daily_rate)), balance)
        self.assertEqual(self.fund.nearest_hundredth(balance - 1000), self.fund.total_growth)  # Check growth variable here as well
        self.assertEqual(1000, self.fund.total_contributions)  # Check total contrib variable
        self.fund.advance_time((date(2001, 8, 8)))
        elapsed_days = (date(2001, 8, 8) - date(2000, 8, 8)).days
        self.assertEqual(365, elapsed_days)
        self.assertEqual(self.fund.nearest_hundredth(1000 * (1 + effective_daily_rate) ** elapsed_days), self.fund.get_balance())

    def test_apy_over_century(self):
        self.fund = Fund(date(1899, 12, 31), "Large Fund")
        self.fund.contribute(1_000_000, date(1900, 1, 1))
        self.fund.advance_time(date(1900, 1, 1))
        self.fund.set_apy(5.0)
        self.fund.advance_time(date(2000, 1, 1))
        elapsed_days = (date(2000, 1, 1) - date(1900, 1, 1)).days
        self.assertEqual(self.fund.nearest_hundredth((1000000 * (1 + self.fund.daily_rate) ** elapsed_days)), self.fund.get_balance())
        self.assertEqual(self.fund.nearest_hundredth(self.fund.balance - 1_000_000), self.fund.total_growth)


    def test_one_day_lose_all(self):
        self.fund.advance_time(date(2000, 1, 1))
        self.fund.set_daily_rate(-1)
        self.fund.balance = 100
        self.fund.advance_time(date(2000, 1, 2))
        self.assertEqual(0, self.fund.get_balance())

    def test_negative_daily_rate(self):
        self.fund.advance_time(date(2000, 1, 1))
        self.fund.set_daily_rate(-0.01)
        self.fund.balance = 100
        self.fund.advance_time(date(2000, 1, 2))
        self.assertEqual(99, self.fund.get_balance())

    def test_lose_all_over_year(self):
        self.fund.advance_time(date(2000, 1, 1))
        self.fund.set_apy(-100)
        self.fund.balance = 100
        self.fund.advance_time(date(2001, 1, 1))
        self.assertEqual(0, self.fund.get_balance())

    def test_apply_interest_only_after_contributions(self):
        self.fund.set_daily_rate(.01)
        self.fund.contribute(1.00, date(1978, 6, 1), frequency=Frequency.SEMIMONTHLY)
        self.fund.advance_time(date(1978, 6, 15))
        self.assertEqual(self.fund.nearest_hundredth(1 * (1.01 ** 14) + 1), self.fund.get_balance())  # 14 days of growth on $1 and another $1
        balance = self.fund.get_balance()
        self.fund.advance_time(date(1978, 7, 15))
        # Accrue interest 16 days until July 1st, add $1, accrue 14 more days, add $1
        self.assertEqual(self.fund.nearest_hundredth((balance * (1.01 ** 16) + 1) * (1.01 ** 14) + 1), self.fund.get_balance())

    def test_cannot_go_negative(self):
        self.fund.set_apy(0)
        self.fund.contribute(10000, date(1978, 1, 1), frequency=Frequency.ONCE)
        self.fund.contribute(-30000, date(1978, 2, 1), frequency=Frequency.ONCE)
        self.fund.advance_time(date(1978, 2, 1))
        self.assertEqual(0, self.fund.get_balance())
        insufficient_hist = [h for h in self.fund.history if h.type == FundTransactionType.INSUFFICIENT_FUNDS]
        self.assertEqual(1, len(insufficient_hist))

    def test_cannot_go_negative_periodic(self):
        self.fund.balance = 500
        self.fund.contribute(-1000, date(1978, 3, 1), frequency=Frequency.MONTHLY)
        self.fund.advance_time(date(1979, 2, 1))
        self.assertEqual(0, self.fund.get_balance())
        insufficient_hist = [h for h in self.fund.history if h.type == FundTransactionType.INSUFFICIENT_FUNDS]
        self.assertEqual(12, len(insufficient_hist))

    def test_can_apply_inflation(self):
        self.fund.set_inflation_rate(5)
        self.fund.set_apy(0)
        self.fund.contribute(1, date(2001, 1, 1), Frequency.SEMIMONTHLY)
        self.fund.contribute(100, date(2001, 1, 1), Frequency.ONCE)
        self.fund.advance_time(date(2001, 1, 14))
        # Check that the previous year's inflation rate is applied to future contributions/withdrawals
        balance = self.fund.get_balance()
        self.assertEqual(105 + 1.05, balance)
        # Zero the balance and this time make sure that after 2 years, inflation is applied twice, once each year
        self.fund.balance = 0
        self.fund.set_inflation_rate(10)
        self.fund.contribute(1, date(2001, 1, 15), Frequency.SEMIMONTHLY)
        self.fund.advance_time(date(2003, 1, 14))
        self.assertEqual(self.fund.nearest_hundredth(23 * 1 + 24 * 1.1 + 1 * 1.1 * 1.1), self.fund.get_balance())

    def test_end_of_year_accounting(self):
        self.fund.contribute(1, date(2001, 1, 15), Frequency.MONTHLY)
        self.fund.advance_time(date(2001, 2, 15))
        self.fund.advance_time(date(2001, 3, 15))
        self.fund.advance_time(date(2001, 4, 15))
        self.fund.advance_time(date(2002, 1, 15))
        apy_hist = [h for h in self.fund.history if h.type == FundTransactionType.APY]
        balance_hist = [h for h in self.fund.history if h.type == FundTransactionType.BALANCE]
        inflation_hist = [h for h in self.fund.history if h.type == FundTransactionType.INFLATION]
        self.assertEqual(2, len(apy_hist))  # Two end of year accounting events
        self.assertEqual(2, len(balance_hist))
        self.assertEqual(2, len(inflation_hist))
        contrib_hist = [h for h in self.fund.history if h.type == FundTransactionType.PERIODIC]
        self.assertEqual(13, len(contrib_hist))
        self.fund.advance_time(date(2003, 1, 15))  # Go another year to ensure yearly contrib summary is only per-year
        contrib_hist = [h for h in self.fund.history if h.type == FundTransactionType.CONTRIBUTION_SUMMARY]
        self.assertEqual(3, len(contrib_hist))
        self.assertEqual(0, contrib_hist[0].amount)
        self.assertEqual(12, contrib_hist[1].amount)
        self.assertEqual(12, contrib_hist[2].amount)


if __name__ == '__main__':
    unittest.main()
