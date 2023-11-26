import unittest
from contribution_schedule import *
from typing import List


class TestContributionSchedule(unittest.TestCase):
    def test_contribute_none_schedule(self):
        co = NoneSchedule()
        amount = co.contribute_until_date(date(1905, 2, 28))
        self.assertEqual(0, amount)

    def test_contributions_no_effect_until_next_date(self):
        for schedule in [MonthlySchedule, SemiMonthlySchedule, BiweeklySchedule]:
            s = schedule(1, date(1900, 1, 1))
            amount = s.contribute_until_date(date(1850, 1, 1))
            self.assertEqual(0, amount)
            amount = s.contribute_until_date(date(1899, 12, 31))
            self.assertEqual(0, amount)
            amount = s.contribute_until_date(date(1900, 1, 1))
            self.assertEqual(1, amount)
            # Doing it again should have no effect for the same date
            amount = s.contribute_until_date(date(1900, 1, 1))
            self.assertEqual(0, amount)
            # Asking to go back into the past will not have an effect
            amount = s.contribute_until_date(date(1700, 4, 17))
            self.assertEqual(0, amount)

        s = SemiMonthlySchedule(1, date(1900, 1, 15))
        amount = s.contribute_until_date(date(1900, 1, 15))
        self.assertEqual(1, amount)

    def test_initial_get_next_contribution_date(self):
        for schedule in [MonthlySchedule, SemiMonthlySchedule, BiweeklySchedule]:
            s = schedule(1, date(1900, 1, 1))
            self.assertEqual(date(1900, 1, 1), s.get_next_contribution_date(), f"While testing {schedule.__name__}")

    def test_one_time_contributions_across_types(self):
        for schedule in [MonthlySchedule, SemiMonthlySchedule, BiweeklySchedule]:
            s = schedule(0, date(1900, 1, 1))
            s.add_one_time_contribution(33, date(1900, 1, 2))
            total = 0.0
            total += s.contribute_until_date(date(1900, 1, 1))
            self.assertEqual(0, total, f"While testing {schedule.__name__}")
            total += s.contribute_until_date(date(1900, 1, 2))
            self.assertEqual(33, total, f"While testing {schedule.__name__}")

    def test_one_contribution_ordering(self):
        s = MonthlySchedule(1, date(1900, 1, 1))
        s.add_one_time_contribution(20, date(1900, 2, 1))
        s.add_one_time_contribution(30, date(1900, 2, 1))  # Add two on same date
        s.add_one_time_contribution(10, date(1900, 1, 9))  # Add one "out of order"
        total = s.contribute_until_date(date(1900, 1, 1))
        self.assertEqual(1, total)
        total += s.contribute_until_date(date(1900, 1, 9))
        self.assertEqual(11, total)
        total += s.contribute_until_date(date(1900, 2, 1))
        self.assertEqual(62, total)

    def test_get_next_contribution_date_with_one_times_added(self):
        s = MonthlySchedule(1, date(1900, 1, 1))
        s.add_one_time_contribution(10, date(1900, 1, 9))
        s.add_one_time_contribution(20, date(1900, 2, 2))
        self.assertEqual(date(1900, 1, 1), s.get_next_contribution_date())
        total = s.contribute_until_date(date(1900, 1, 1))
        self.assertEqual(1, total)
        self.assertEqual(date(1900, 1, 9), s.get_next_contribution_date())
        total += s.contribute_until_date(date(1900, 1, 9))
        self.assertEqual(11, total)
        self.assertEqual(date(1900, 2, 1), s.get_next_contribution_date())
        total += s.contribute_until_date(date(1900, 2, 1))
        self.assertEqual(12, total)
        self.assertEqual(date(1900, 2, 2), s.get_next_contribution_date())
        total += s.contribute_until_date(date(1900, 2, 2))
        self.assertEqual(32, total)
        self.assertEqual(date(1900, 3, 1), s.get_next_contribution_date())

    def test_monthly_schedule(self):
        total = int(0)
        start_date = date(1900, 1, 4)
        s = MonthlySchedule(1, start_date)
        self.assertEqual(start_date-timedelta(days=31), s.last_contribution_date)
        self.assertEqual(start_date, s.get_next_contribution_date())

        total += s.contribute_until_date(date(1900, 1, 3))
        self.assertEqual(start_date-timedelta(days=31), s.last_contribution_date)
        self.assertEqual(start_date, s.get_next_contribution_date())
        self.assertEqual(0, total)  # Nothing contributed yet

        total += s.contribute_until_date(date(1900, 1, 4))  # Monthly pay day reached
        self.assertEqual(date(1900, 1, 4), s.last_contribution_date)
        self.assertEqual(date(1900, 2, 4), s.get_next_contribution_date())
        self.assertEqual(1, total)

        total += s.contribute_until_date(date(1900, 2, 3))  # next month before pay day
        self.assertEqual(date(1900, 1, 4), s.last_contribution_date)
        self.assertEqual(date(1900, 2, 4), s.get_next_contribution_date())
        self.assertEqual(1, total)

        total += s.contribute_until_date(date(1900, 2, 4))  # 2nd monthly comes in
        self.assertEqual(date(1900, 2, 4), s.last_contribution_date)
        self.assertEqual(date(1900, 3, 4), s.get_next_contribution_date())
        self.assertEqual(2, total)

        total += s.contribute_until_date(date(1901, 2, 4))  # 1 year later
        self.assertEqual(date(1901, 2, 4), s.last_contribution_date)
        self.assertEqual(date(1901, 3, 4), s.get_next_contribution_date())
        self.assertEqual(2 + 12, total)

        # Advance to the same date and all should remain the same
        total += s.contribute_until_date(date(1901, 2, 14))
        self.assertEqual(date(1901, 2, 4), s.last_contribution_date)
        self.assertEqual(date(1901, 3, 4), s.get_next_contribution_date())
        self.assertEqual(2 + 12, total)

    def test_biweekly_schedules(self):
        contribution_types: List[BaseContributionSchedule]
        total = 0.0
        start_date = date(1900, 1, 4)

        cbw = BiweeklySchedule(1, start_date)

        self.assertEqual(start_date-timedelta(days=14), cbw.last_contribution_date)
        self.assertEqual(start_date, cbw.get_next_contribution_date())
        self.assertEqual(0, total)  # Nothing contributed yet

        total += cbw.contribute_until_date(date(1900, 1, 3))  # One day just before 1st biweekly
        self.assertEqual(start_date-timedelta(days=14), cbw.last_contribution_date)
        self.assertEqual(0, total)  # Nothing contributed yet

        total += cbw.contribute_until_date(date(1900, 1, 4))  # Biweekly is the first to pay
        self.assertEqual(date(1900, 1, 4), cbw.last_contribution_date)
        self.assertEqual(cbw.last_contribution_date + timedelta(days=14), cbw.get_next_contribution_date())
        self.assertEqual(1, total)

        total += cbw.contribute_until_date(date(1900, 1, 15))  # First semi-monthly
        self.assertEqual(date(1900, 1, 4), cbw.last_contribution_date)
        self.assertEqual(cbw.last_contribution_date + timedelta(days=14), cbw.get_next_contribution_date())
        self.assertEqual(1, total)

        total += cbw.contribute_until_date(date(1900, 2, 1))  # Semi-monthly and Bi-weekly both hit on Feb 1
        self.assertEqual(date(1900, 2, 1), cbw.last_contribution_date)
        self.assertEqual(cbw.last_contribution_date + timedelta(days=14), cbw.get_next_contribution_date())
        self.assertEqual(3, total)

        total += cbw.contribute_until_date(date(1900, 2, 4))  # No change
        self.assertEqual(date(1900, 2, 1), cbw.last_contribution_date)
        self.assertEqual(cbw.last_contribution_date + timedelta(days=14), cbw.get_next_contribution_date())
        self.assertEqual(3, total)

        total += cbw.contribute_until_date(date(1901, 2, 4))  # 1 year later
        self.assertEqual(date(1901, 1, 31), cbw.last_contribution_date)
        self.assertEqual(cbw.last_contribution_date + timedelta(days=14), cbw.get_next_contribution_date())
        self.assertEqual(3 + 52//2, total)

        # Move a few more days to get the next biweekly on Thursday 1901, 2, 7
        total += cbw.contribute_until_date(date(1901, 2, 14))
        self.assertEqual(date(1901, 2, 14), cbw.last_contribution_date)
        self.assertEqual(cbw.last_contribution_date + timedelta(days=14), cbw.get_next_contribution_date())
        self.assertEqual(3 + 52/2 + 1, total)

        # Advance to the same date and all should remain the same
        total += cbw.contribute_until_date(date(1901, 2, 14))
        self.assertEqual(date(1901, 2, 14), cbw.last_contribution_date)
        self.assertEqual(3 + 52/2 + 1, total)

    def test_semi_monthly_schedules(self):
        contribution_types: List[BaseContributionSchedule]
        total = 0.0
        start_date = date(1900, 1, 4)

        csm = SemiMonthlySchedule(1, start_date)
        contribution_types = [csm]

        self.assertEqual(date(1900, 1, 1), csm.last_contribution_date)
        self.assertEqual(date(1900, 1, 15), csm.get_next_contribution_date())
        self.assertEqual(0, total)  # Nothing contributed yet

        total += csm.contribute_until_date(date(1900, 1, 4))  # Go to the start date, but not 1st nor 15th
        self.assertEqual(date(1900, 1, 1), csm.last_contribution_date)
        self.assertEqual(date(1900, 1, 15), csm.get_next_contribution_date())
        self.assertEqual(0, total)

        total += csm.contribute_until_date(date(1900, 1, 15))  # First semi-monthly
        self.assertEqual(date(1900, 1, 15), csm.last_contribution_date)
        self.assertEqual(date(1900, 2, 1), csm.get_next_contribution_date())
        self.assertEqual(1, total)

        total += csm.contribute_until_date(date(1900, 2, 1))  # Next semi-monthly
        self.assertEqual(date(1900, 2, 1), csm.last_contribution_date)
        self.assertEqual(date(1900, 2, 15), csm.get_next_contribution_date())
        self.assertEqual(2, total)

        total += csm.contribute_until_date(date(1900, 1, 15))  # try to hit last date, in the past
        self.assertEqual(date(1900, 2, 1), csm.last_contribution_date)
        self.assertEqual(2, total)

        total += csm.contribute_until_date(date(1900, 2, 4))  # No change
        self.assertEqual(date(1900, 2, 1), csm.last_contribution_date)
        self.assertEqual(date(1900, 2, 15), csm.get_next_contribution_date())
        self.assertEqual(2, total)

        total += csm.contribute_until_date(date(1900, 3, 16))  # Change date's month and half it lies in
        self.assertEqual(date(1900, 3, 15), csm.last_contribution_date)
        self.assertEqual(date(1900, 4, 1), csm.get_next_contribution_date())
        self.assertEqual(5, total)

        total += csm.contribute_until_date(date(1901, 2, 4))  # 1 year later
        self.assertEqual(date(1901, 2, 1), csm.last_contribution_date)
        self.assertEqual(date(1901, 2, 15), csm.get_next_contribution_date())
        self.assertEqual(2 + 24, total)

        # Move a few more days to get the next biweekly on Thursday 1901, 2, 7
        total += csm.contribute_until_date(date(1901, 2, 14))
        self.assertEqual(date(1901, 2, 1), csm.last_contribution_date)
        self.assertEqual(date(1901, 2, 15), csm.get_next_contribution_date())
        self.assertEqual(2 + 24, total)

        # Advance to the same date and all should remain the same
        total += csm.contribute_until_date(date(1901, 2, 14))
        self.assertEqual(date(1901, 2, 1), csm.last_contribution_date)
        self.assertEqual(2 + 24, total)


if __name__ == '__main__':
    unittest.main()
