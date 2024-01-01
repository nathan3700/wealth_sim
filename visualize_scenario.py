from datetime import date, timedelta
from fund import Fund
from contribution_schedule import Frequency
import csv
from scipy.stats import t, norm
import matplotlib.pyplot as plt
import numpy as np
import random


class RetirementScenario:
    def __init__(self):
        self.years_sp500, self.returns_sp500 = self.get_data_from_csv("sp500_returns_1928_2022.csv")
        years_inflation, inflation_data = self.get_data_from_csv("us_BLS_cpiu_inflation_1928_2022.csv")
        self.sp500_by_year = dict()
        self.inflation_by_year = dict()
        self.random_past_years = []
        for index in range(len(self.years_sp500)):
            year = self.years_sp500[index]
            self.sp500_by_year[year] = self.returns_sp500[index]
            self.inflation_by_year[year] = inflation_data[index]
            self.random_past_years.append(year)
        random.seed(26)
        random.shuffle(self.random_past_years)
        self.use_historical_sp500 = True
        self.use_historical_inflation = True
        self.default_apy = 4.5
        start_year = 2000
        retirement_year = 2030
        begin_withdrawal_year = 2035
        death_year = 2060

        self.fund = Fund(date(start_year - 1, 12, 31), "Sample Fund")
        self.fund.contribute(1000, date(start_year, 1, 1), Frequency.MONTHLY)
        year_index = 0
        year = start_year
        while year < retirement_year:
            self.update_apy(year_index)
            self.fund.advance_time(date(year, 1, 1))
            year += 1
            year_index += 1

        retirement_date = self.fund.get_current_date()
        self.fund.contribute(0, retirement_date + timedelta(days=1), Frequency.NONE)

        while year < begin_withdrawal_year:
            self.update_apy(year_index)
            self.fund.advance_time(date(year, 1, 1))
            year += 1
            year_index += 1

        draw_down_date = self.fund.get_current_date()
        self.fund.contribute(-5000, draw_down_date + timedelta(days=1), Frequency.MONTHLY)
        while year <= death_year:
            self.update_apy(year_index)
            self.fund.advance_time(date(year, 1, 1))
            year += 1
            year_index += 1

        print(f"Last year {year}")

    def update_apy(self, year_index):
        if self.use_historical_sp500:
            new_apy = self.sp500_by_year[self.random_past_years[year_index]]
        else:
            new_apy = self.default_apy
        if self.use_historical_inflation:
            new_apy -= self.inflation_by_year[self.random_past_years[year_index]]
        self.fund.set_apy(new_apy)

    def visualize_results(self):
        years = []
        balances = []
        for h in self.fund.balance_history:
            years.append(h.date.year)
            balances.append(h.amount)
        apy_values = [apy for apy in self.fund.apy_history]

        fig, ax1 = plt.subplots(sharex=True)
        ax2 = ax1.twinx()
        assert(len(balances) == len(apy_values))

        ax1.bar(years, apy_values, color='r', label="APY")
        ax1.set_ylabel("APY")
        label_info = f"Balance from {self.fund.balance_history[0].date} " + f" to {self.fund.balance_history[len(self.fund.balance_history) - 1].date}"
        ax2.plot(years, balances, color='b', label=label_info, )
        ax2.set_ylabel('Balance in $')

        plt.xlabel("Years")
        plt.title(self.fund.name)

        ax1.legend()
        ax2.legend()
        plt.show()

    def visualize_market_returns_distribution(self):
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
    def get_data_from_csv(file: str):
        csv_file_handle = open(file, newline='')  # csv.reader does its own newline handling
        header_row = []
        col1 = []
        col2 = []
        for row in csv.reader(csv_file_handle):
            if len(header_row) == 0:
                header_row = row
            else:
                col1.append(int(row[0]))
                yearly_return = row[1].strip("%")
                col2.append(float(yearly_return))
        csv_file_handle.close()
        return col1, col2


if __name__ == '__main__':
    s = RetirementScenario()
    s.visualize_results()
