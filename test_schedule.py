import unittest
from transfer_schedule import *
from typing import List


class TestContributionSchedule(unittest.TestCase):

    @staticmethod
    def add_up(contributions: List[FundTransaction]):
        amounts = [c.amount for c in contributions]
        return sum(amounts)

    def test_contribute_none_schedule(self):
        co = NoneSchedule()
        amount = co.get_transfers_until(date(1905, 2, 28))
        self.assertEqual([], amount)

    def test_contributions_no_effect_until_next_date(self):
        for schedule in [MonthlySchedule, SemiMonthlySchedule, BiweeklySchedule]:
            s = schedule(1, date(1900, 1, 1))
            amounts = s.get_transfers_until(date(1850, 1, 1))
            self.assertEqual(0, self.add_up(amounts))
            amounts = s.get_transfers_until(date(1899, 12, 31))
            self.assertEqual(0, self.add_up(amounts))
            amounts = s.get_transfers_until(date(1900, 1, 1))
            self.assertEqual(1, self.add_up(amounts))
            # Doing it again should have no effect for the same date
            amounts = s.get_transfers_until(date(1900, 1, 1))
            self.assertEqual(0, self.add_up(amounts))
            # Asking to go back into the past will not have an effect
            amounts = s.get_transfers_until(date(1700, 4, 17))
            self.assertEqual(0, self.add_up(amounts))

        s = SemiMonthlySchedule(1, date(1900, 1, 15))
        amounts = s.get_transfers_until(date(1900, 1, 15))
        self.assertEqual(1, self.add_up(amounts))

    def test_initial_get_next_contribution_date(self):
        for schedule in [MonthlySchedule, SemiMonthlySchedule, BiweeklySchedule]:
            s = schedule(1, date(1900, 1, 1))
            self.assertEqual(date(1900, 1, 1), s.get_next_transfer_date(), f"While testing {schedule.__name__}")

    def test_one_time_contributions_across_types(self):
        for schedule in [MonthlySchedule, SemiMonthlySchedule, BiweeklySchedule]:
            s = schedule(0, date(1900, 1, 1))
            s.add_one_time_transfer(33, date(1900, 1, 2))
            received = []
            received += s.get_transfers_until(date(1900, 1, 1))
            self.assertEqual(0, self.add_up(received), f"While testing {schedule.__name__}")
            received += s.get_transfers_until(date(1900, 1, 2))
            self.assertEqual(33, self.add_up(received), f"While testing {schedule.__name__}")

    def test_one_contribution_ordering(self):
        s = MonthlySchedule(1, date(1900, 1, 1))
        s.add_one_time_transfer(20, date(1900, 2, 1))
        s.add_one_time_transfer(30, date(1900, 2, 1))  # Add two on same date
        s.add_one_time_transfer(10, date(1900, 1, 9))  # Add one "out of order"
        received = s.get_transfers_until(date(1900, 1, 1))
        self.assertEqual(1, self.add_up(received))
        received += s.get_transfers_until(date(1900, 1, 9))
        self.assertEqual(11, self.add_up(received))
        received += s.get_transfers_until(date(1900, 2, 1))
        self.assertEqual(62, self.add_up(received))

    def test_get_next_contribution_date_with_one_times_added(self):
        s = MonthlySchedule(1, date(1900, 1, 1))
        s.add_one_time_transfer(10, date(1900, 1, 9))
        s.add_one_time_transfer(20, date(1900, 2, 2))
        self.assertEqual(date(1900, 1, 1), s.get_next_transfer_date())
        received = s.get_transfers_until(date(1900, 1, 1))
        self.assertEqual(1, self.add_up(received))
        self.assertEqual(date(1900, 1, 9), s.get_next_transfer_date())
        received += s.get_transfers_until(date(1900, 1, 9))
        self.assertEqual(11, self.add_up(received))
        self.assertEqual(date(1900, 2, 1), s.get_next_transfer_date())
        received += s.get_transfers_until(date(1900, 2, 1))
        self.assertEqual(12, self.add_up(received))
        self.assertEqual(date(1900, 2, 2), s.get_next_transfer_date())
        received += s.get_transfers_until(date(1900, 2, 2))
        self.assertEqual(32, self.add_up(received))
        self.assertEqual(date(1900, 3, 1), s.get_next_transfer_date())

    def test_monthly_schedule(self):
        received = []
        start_date = date(1900, 1, 4)
        s = MonthlySchedule(1, start_date)
        self.assertEqual(start_date - timedelta(days=31), s.last_transfer_date)
        self.assertEqual(start_date, s.get_next_transfer_date())

        received += s.get_transfers_until(date(1900, 1, 3))
        self.assertEqual(start_date - timedelta(days=31), s.last_transfer_date)
        self.assertEqual(start_date, s.get_next_transfer_date())
        self.assertEqual(0, self.add_up(received))  # Nothing contributed yet

        received += s.get_transfers_until(date(1900, 1, 4))  # Monthly pay day reached
        self.assertEqual(date(1900, 1, 4), s.last_transfer_date)
        self.assertEqual(date(1900, 2, 4), s.get_next_transfer_date())
        self.assertEqual(1, self.add_up(received))

        received += s.get_transfers_until(date(1900, 2, 3))  # next month before pay day
        self.assertEqual(date(1900, 1, 4), s.last_transfer_date)
        self.assertEqual(date(1900, 2, 4), s.get_next_transfer_date())
        self.assertEqual(1, self.add_up(received))

        received += s.get_transfers_until(date(1900, 2, 4))  # 2nd monthly comes in
        self.assertEqual(date(1900, 2, 4), s.last_transfer_date)
        self.assertEqual(date(1900, 3, 4), s.get_next_transfer_date())
        self.assertEqual(2, self.add_up(received))

        received += s.get_transfers_until(date(1901, 2, 4))  # 1 year later
        self.assertEqual(date(1901, 2, 4), s.last_transfer_date)
        self.assertEqual(date(1901, 3, 4), s.get_next_transfer_date())
        self.assertEqual(2 + 12, self.add_up(received))

        # Advance to the same date and all should remain the same
        received += s.get_transfers_until(date(1901, 2, 14))
        self.assertEqual(date(1901, 2, 4), s.last_transfer_date)
        self.assertEqual(date(1901, 3, 4), s.get_next_transfer_date())
        self.assertEqual(2 + 12, self.add_up(received))

    def test_biweekly_schedules(self):
        contribution_types: List[BaseTransferSchedule]
        received = []
        start_date = date(1900, 1, 4)

        cbw = BiweeklySchedule(1, start_date)

        self.assertEqual(start_date - timedelta(days=14), cbw.last_transfer_date)
        self.assertEqual(start_date, cbw.get_next_transfer_date())
        self.assertEqual(0, self.add_up(received))  # Nothing contributed yet

        received += cbw.get_transfers_until(date(1900, 1, 3))  # One day just before 1st biweekly
        self.assertEqual(start_date - timedelta(days=14), cbw.last_transfer_date)
        self.assertEqual(0, self.add_up(received))  # Nothing contributed yet

        received += cbw.get_transfers_until(date(1900, 1, 4))  # Biweekly is the first to pay
        self.assertEqual(date(1900, 1, 4), cbw.last_transfer_date)
        self.assertEqual(cbw.last_transfer_date + timedelta(days=14), cbw.get_next_transfer_date())
        self.assertEqual(1, self.add_up(received))

        received += cbw.get_transfers_until(date(1900, 1, 15))  # First semi-monthly
        self.assertEqual(date(1900, 1, 4), cbw.last_transfer_date)
        self.assertEqual(cbw.last_transfer_date + timedelta(days=14), cbw.get_next_transfer_date())
        self.assertEqual(1, self.add_up(received))

        received += cbw.get_transfers_until(date(1900, 2, 1))  # Semi-monthly and Bi-weekly both hit on Feb 1
        self.assertEqual(date(1900, 2, 1), cbw.last_transfer_date)
        self.assertEqual(cbw.last_transfer_date + timedelta(days=14), cbw.get_next_transfer_date())
        self.assertEqual(3, self.add_up(received))

        received += cbw.get_transfers_until(date(1900, 2, 4))  # No change
        self.assertEqual(date(1900, 2, 1), cbw.last_transfer_date)
        self.assertEqual(cbw.last_transfer_date + timedelta(days=14), cbw.get_next_transfer_date())
        self.assertEqual(3, self.add_up(received))

        received += cbw.get_transfers_until(date(1901, 2, 4))  # 1 year later
        self.assertEqual(date(1901, 1, 31), cbw.last_transfer_date)
        self.assertEqual(cbw.last_transfer_date + timedelta(days=14), cbw.get_next_transfer_date())
        self.assertEqual(3 + 52//2, self.add_up(received))

        # Move a few more days to get the next biweekly on Thursday 1901, 2, 7
        received += cbw.get_transfers_until(date(1901, 2, 14))
        self.assertEqual(date(1901, 2, 14), cbw.last_transfer_date)
        self.assertEqual(cbw.last_transfer_date + timedelta(days=14), cbw.get_next_transfer_date())
        self.assertEqual(3 + 52/2 + 1, self.add_up(received))

        # Advance to the same date and all should remain the same
        received += cbw.get_transfers_until(date(1901, 2, 14))
        self.assertEqual(date(1901, 2, 14), cbw.last_transfer_date)
        self.assertEqual(3 + 52/2 + 1, self.add_up(received))

    def test_semi_monthly_schedules(self):
        contribution_types: List[BaseTransferSchedule]
        received = []
        start_date = date(1900, 1, 4)

        csm = SemiMonthlySchedule(1, start_date)
        contribution_types = [csm]

        self.assertEqual(date(1900, 1, 1), csm.last_transfer_date)
        self.assertEqual(date(1900, 1, 15), csm.get_next_transfer_date())
        self.assertEqual(0, self.add_up(received))  # Nothing contributed yet

        received += csm.get_transfers_until(date(1900, 1, 4))  # Go to the start date, but not 1st nor 15th
        self.assertEqual(date(1900, 1, 1), csm.last_transfer_date)
        self.assertEqual(date(1900, 1, 15), csm.get_next_transfer_date())
        self.assertEqual(0, self.add_up(received))

        received += csm.get_transfers_until(date(1900, 1, 15))  # First semi-monthly
        self.assertEqual(date(1900, 1, 15), csm.last_transfer_date)
        self.assertEqual(date(1900, 2, 1), csm.get_next_transfer_date())
        self.assertEqual(1, self.add_up(received))

        received += csm.get_transfers_until(date(1900, 2, 1))  # Next semi-monthly
        self.assertEqual(date(1900, 2, 1), csm.last_transfer_date)
        self.assertEqual(date(1900, 2, 15), csm.get_next_transfer_date())
        self.assertEqual(2, self.add_up(received))

        received += csm.get_transfers_until(date(1900, 1, 15))  # try to hit last date, in the past
        self.assertEqual(date(1900, 2, 1), csm.last_transfer_date)
        self.assertEqual(2, self.add_up(received))

        received += csm.get_transfers_until(date(1900, 2, 4))  # No change
        self.assertEqual(date(1900, 2, 1), csm.last_transfer_date)
        self.assertEqual(date(1900, 2, 15), csm.get_next_transfer_date())
        self.assertEqual(2, self.add_up(received))

        received += csm.get_transfers_until(date(1900, 3, 16))  # Change date's month and half it lies in
        self.assertEqual(date(1900, 3, 15), csm.last_transfer_date)
        self.assertEqual(date(1900, 4, 1), csm.get_next_transfer_date())
        self.assertEqual(5, self.add_up(received))

        received += csm.get_transfers_until(date(1901, 2, 4))  # 1 year later
        self.assertEqual(date(1901, 2, 1), csm.last_transfer_date)
        self.assertEqual(date(1901, 2, 15), csm.get_next_transfer_date())
        self.assertEqual(2 + 24, self.add_up(received))

        # Move a few more days to get the next biweekly on Thursday 1901, 2, 7
        received += csm.get_transfers_until(date(1901, 2, 14))
        self.assertEqual(date(1901, 2, 1), csm.last_transfer_date)
        self.assertEqual(date(1901, 2, 15), csm.get_next_transfer_date())
        self.assertEqual(2 + 24, self.add_up(received))

        # Advance to the same date and all should remain the same
        received += csm.get_transfers_until(date(1901, 2, 14))
        self.assertEqual(date(1901, 2, 1), csm.last_transfer_date)
        self.assertEqual(2 + 24, self.add_up(received))

    def test_inflate_contributions(self):
        start_date = date(1800, 5, 5)
        csm = SemiMonthlySchedule(1000, start_date)
        csm.add_one_time_transfer(10, start_date)
        csm.inflate_transfer_amounts(20)
        self.assertEqual(1200, csm.amount)
        for one_time_date, one_time in csm.future_one_time_transfers:
            self.assertEqual(12, one_time)




if __name__ == '__main__':
    unittest.main()
