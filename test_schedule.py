import unittest
from contribution_schedule import *
from typing import List


class TestContributionSchedule(unittest.TestCase):
    def test_contribute_none_schedule(self):
        co = NoneSchedule()
        amount = co.contribute_until_date(date(1905, 2, 28))
        self.assertEqual(0, amount)

    def test_contribution_schedules(self):
        contribution_types: List[BaseContributionSchedule]
        totals = [int(0)] * 3
        start_date = date(1900, 1, 4)
        last_contribution_dates = [start_date] * 3

        def advance_contributions_until(next_date: date):
            for i, c in enumerate(contribution_types):
                totals[i] += c.contribute_until_date(next_date)
                last_contribution_dates[i] = c.last_contribution_date
        cm = MonthlySchedule(1, start_date)
        cbw = BiweeklySchedule(1, start_date)
        csm = SemiMonthlySchedule(1, start_date)
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
        self.assertEqual([date(1901, 2, 4),  date(1901, 1, 31), date(1901, 2, 1)], last_contribution_dates)
        self.assertEqual([1 + 12, 2 + 52//2, 2 + 24], totals)

        # Move a few more days to get the next biweekly on Thursday 1901, 2, 7
        advance_contributions_until(date(1901, 2, 14))
        self.assertEqual([date(1901, 2, 4),  date(1901, 2, 14), date(1901, 2, 1)], last_contribution_dates)
        self.assertEqual([1 + 12, 2 + 52/2 + 1, 2 + 24], totals)

        # Advance to the same date and all should remain the same
        advance_contributions_until(date(1901, 2, 14))
        self.assertEqual([date(1901, 2, 4),  date(1901, 2, 14), date(1901, 2, 1)], last_contribution_dates)
        self.assertEqual([1 + 12, 2 + 52/2 + 1, 2 + 24], totals)

        # Go into the past and nothing should change
        advance_contributions_until(date(1899, 1, 17))
        self.assertEqual([date(1901, 2, 4),  date(1901, 2, 14), date(1901, 2, 1)], last_contribution_dates)
        self.assertEqual([1 + 12, 2 + 52/2 + 1, 2 + 24], totals)


if __name__ == '__main__':
    unittest.main()
