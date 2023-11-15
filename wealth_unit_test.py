import unittest
from datetime import datetime, timedelta
from fund import Frequency, Fund


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.fund = Fund()

    def test_can_instantiate_fund(self):
        self.assertIsNotNone(self.fund)

    def test_can_contribute_to_fund(self):
        self.fund.contribute(10_000.00)
        balance = self.fund.get_balance()
        self.assertEqual(balance, 10_000)

    def test_can_contribute_monthly(self):
        start_day = datetime(2023, 10, 1)
        self.fund.contribute(1000, date=start_day, frequency=Frequency.MONTHLY)
        self.fund.advance_time(datetime(2023, 12, 1))
        balance = self.fund.get_balance()
        self.assertEqual(balance, 2000)

    def test_can_contribute_biweekly(self):
        start_day = datetime(2023, 10, 1)
        self.fund.contribute(1000, date=start_day, frequency=Frequency.BIWEEKLY)
        self.fund.advance_time(start_day + timedelta(days=6, weeks=3))
        balance = self.fund.get_balance()
        self.assertEqual(balance, 1000)
        self.fund.advance_time(start_day + timedelta(weeks=4))
        self.assertEqual(2000, self.fund.get_balance())


if __name__ == '__main__':
    unittest.main()
