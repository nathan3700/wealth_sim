import unittest
import matplotlib.pyplot as plt
from datetime import date, timedelta
from fund import Fund
from contribution_schedule import Frequency


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.fund = Fund(date(1999, 12, 31), "Sample Fund")
        self.fund.contribute(1000, date(2000, 1, 1), Frequency.MONTHLY)
        self.fund.set_apy(5.0)
        for year in range(30 + 1):
            self.fund.advance_time(date(2000 + year, 1, 1))
        retirement_date = self.fund.get_current_date()
        self.fund.contribute(0, retirement_date + timedelta(days=1), Frequency.NONE)
        # Retire but postpone withdrawals for 5 years
        for year in range(5 + 1):
            self.fund.advance_time(date(retirement_date.year + year, 1, 1))
        draw_down_date = self.fund.get_current_date()
        self.fund.contribute(-5000, draw_down_date + timedelta(days=1), Frequency.MONTHLY)
        for year in range(25 + 1):
            self.fund.advance_time(date(draw_down_date.year + year, 1, 1))

    def test_plot_fund(self):
        x_values = [h.date.year for h in self.fund.balance_history]
        y_values = [h.amount for h in self.fund.balance_history]

        f = plt.plot(x_values, y_values, label=f"Balance from {self.fund.balance_history[0].date} " +
        f" to {self.fund.balance_history[len(self.fund.balance_history) - 1].date}")

        plt.xlabel("Years")
        plt.ylabel('Balance in $')
        plt.title(self.fund.name)

        plt.legend()
        plt.show()


if __name__ == '__main__':
    unittest.main()
