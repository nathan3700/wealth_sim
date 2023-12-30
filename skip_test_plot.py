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
        random.seed(27)
        random.shuffle(self.returns_sp500)
        start_year = 2000
        retirement_year = 2030
        begin_withdrawal_year = 2035
        death_year = 2060

        self.fund = Fund(date(start_year - 1, 12, 31), "Sample Fund")
        self.fund.contribute(1000, date(start_year, 1, 1), Frequency.MONTHLY)
        self.fund.set_apy(5.0)
        year_index = 0
        year = start_year
        while year < retirement_year:
            self.fund.set_apy(self.returns_sp500[year_index])
            self.fund.advance_time(date(year, 1, 1))
            year += 1
            year_index += 1
            # print(year)

        retirement_date = self.fund.get_current_date()
        self.fund.contribute(0, retirement_date + timedelta(days=1), Frequency.NONE)

        while year < begin_withdrawal_year:
            self.fund.set_apy(self.returns_sp500[year_index])
            self.fund.advance_time(date(year, 1, 1))
            year += 1
            year_index += 1
            # print(year)

        draw_down_date = self.fund.get_current_date()
        self.fund.contribute(-5000, draw_down_date + timedelta(days=1), Frequency.MONTHLY)
        while year <= death_year:
            self.fund.set_apy(self.returns_sp500[year_index])
            self.fund.advance_time(date(year, 1, 1))
            year += 1
            year_index += 1
            # print(year)

        print(f"Last year {year}")

    def test_plot_fund(self):
        x_values = [h.date.year for h in self.fund.balance_history]
        y_values = [h.amount for h in self.fund.balance_history]

        fig, ax1 = plt.subplots(sharex=True)
        ax2 = ax1.twinx()

        label_info = f"Balance from {self.fund.balance_history[0].date} " + f" to {self.fund.balance_history[len(self.fund.balance_history) - 1].date}"
        print(label_info)
        ax1.plot(x_values, y_values, color='b', label=label_info)

        ax2.plot(x_values, self.returns_sp500[0:len(y_values)], color='r', label="APY")

        plt.xlabel("Years")
        ax1.set_ylabel('Balance in $')
        ax2.set_ylabel("APY")
        plt.title(self.fund.name)

        ax1.legend()
        ax2.legend()
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
