import unittest
from datetime import date, timedelta
from fund import Fund
from contribution_schedule import Frequency
import csv
from scipy.stats import t, norm
import matplotlib.pyplot as plt
import numpy as np
import random


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.years_sp500, self.returns_sp500 = self.get_sp500_returns_from_csv()
        random.seed(26)

        self.fund = Fund(date(1999, 12, 31), "Sample Fund")
        self.fund.contribute(1000, date(2000, 1, 1), Frequency.MONTHLY)
        self.fund.set_apy(5.0)
        for year in range(30 + 1):
            self.fund.set_apy(self.returns_sp500[random.randrange(0, len(self.returns_sp500))])
            self.fund.advance_time(date(2000 + year, 1, 1))

        retirement_date = self.fund.get_current_date()
        self.fund.contribute(0, retirement_date + timedelta(days=1), Frequency.NONE)
        # Retire but postpone withdrawals for 5 years
        for year in range(5 + 1):
            self.fund.set_apy(self.returns_sp500[random.randrange(0, len(self.returns_sp500))])
            self.fund.advance_time(date(retirement_date.year + year, 1, 1))
        draw_down_date = self.fund.get_current_date()
        self.fund.contribute(-5000, draw_down_date + timedelta(days=1), Frequency.MONTHLY)
        for year in range(25 + 1):
            self.fund.set_apy(self.returns_sp500[random.randrange(0, len(self.returns_sp500))])
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

    @unittest.skip
    def test_shape_market_returns(self):
        # See https://papers.ssrn.com/sol3/papers.cfm?abstract_id=955639
        # Egan proposes a t-distribution for SP500 returns with nu=3.6 to widen the tails to
        # increase the likelihood of more extreme returns
        # Also see https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histretSP.html  for historical SP500
        returns = self.returns_sp500

        location = 11.5  # Mean of returns (about 11.5%)
        scale = 23  # Standard deviation

        # Degrees of freedom parameter for the t-distribution
        degrees_of_freedom = 3.6

        # Generate random samples following a t-distribution
        samples = t.rvs(df=degrees_of_freedom, loc=location, scale=scale, size=200)

        # Plotting the histogram of generated samples
        # plt.hist(samples, bins=50, density=True, alpha=0.5, color='blue', edgecolor='black')
        plt.hist(returns, bins=25, density=True, alpha=0.5, color='green', edgecolor='black')

        # Plotting the probability density function
        x = np.linspace(-100, 100, 1000)
        plt.plot(x, t.pdf(x, df=degrees_of_freedom, loc=location, scale=scale), 'r-', lw=2, label='PDF T-dist')
        plt.plot(x, norm.pdf(x, loc=location, scale=scale), 'black', lw=2, label='PDF Norm')

        plt.xlabel('Value')
        plt.ylabel('Density')
        plt.title('SP500 Returns against normal and t-distribution curves')
        plt.legend()
        plt.show()

    @staticmethod
    def get_sp500_returns_from_csv():
        returns_csv = open("sp500_returns_1928_2022.csv", newline='')  # csv.reader does its own newline handling
        header_row = []
        years = []
        returns = []
        for row in csv.reader(returns_csv):
            if len(header_row) == 0:
                header_row = row
            else:
                years.append(int(row[0]))
                yearly_return = row[1].strip("%")
                returns.append(float(yearly_return))
        returns_csv.close()
        return years, returns


if __name__ == '__main__':
    unittest.main()
