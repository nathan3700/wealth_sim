from datetime import date, timedelta
from wealth_fund import Fund, FundTransactionType, FundTransaction
from contribution_schedule import Frequency
import csv
from scipy.stats import t, norm
import matplotlib.pyplot as plt
import numpy as np
import random
from typing import List


class RetirementScenario:
    def __init__(self):
        self.scenario_name = "Sample Fund"
        # Inputs
        self.monthly_contribution = 500
        self.retirement_year = 2030
        self.start_year = 2000
        self.death_year = 2060
        self.begin_withdrawal_year = 2035
        self.retirement_monthly_withdrawal = 5000
        self.use_historical_sp500 = True
        self.reduce_apy_by_inflation = False
        self.apply_inflation_to_contributions = True
        self.default_apy = 4.5
        # Outputs
        self.results: List[List[FundTransaction]] = []

        # State
        self.sp500_by_year = dict()
        self.inflation_by_year = dict()
        self.past_years = []
        self.random_past_years = []
        self.load_historical_data()

    def load_historical_data(self):
        years_sp500, returns_sp500 = self.get_data_from_csv("sp500_returns_1928_2022.csv")
        years_inflation, inflation_data = self.get_data_from_csv("us_BLS_cpiu_inflation_1928_2022.csv")
        for index in range(len(years_sp500)):
            year = years_sp500[index]
            self.sp500_by_year[year] = returns_sp500[index]
            self.inflation_by_year[year] = inflation_data[index]
            self.past_years.append(year)

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

    def run_scenario(self, seeds: []):
        for seed in seeds:
            self.randomize_historical_order(seed)
            fund = Fund(date(self.start_year - 1, 12, 31), self.scenario_name)
            fund.contribute(self.monthly_contribution, date(self.start_year, 1, 1), Frequency.MONTHLY)
            year_index = 0
            year = self.start_year
            while year < self.retirement_year:
                self.update_apy(year_index, fund)
                fund.advance_time(date(year, 1, 1))
                year += 1
                year_index += 1
            retirement_date = fund.get_current_date()
            fund.contribute(0, retirement_date + timedelta(days=1), Frequency.NONE)
            while year < self.begin_withdrawal_year:
                self.update_apy(year_index, fund)
                fund.advance_time(date(year, 1, 1))
                year += 1
                year_index += 1
            draw_down_date = fund.get_current_date()
            fund.contribute(-self.retirement_monthly_withdrawal, draw_down_date + timedelta(days=1), Frequency.MONTHLY)
            while year <= self.death_year:
                self.update_apy(year_index, fund)
                fund.advance_time(date(year, 1, 1))
                year += 1
                year_index += 1

            self.results.append(fund.history)

    def randomize_historical_order(self, seed: int):
        random.seed(seed)
        self.random_past_years = [y for y in self.past_years]  # Duplicate
        random.shuffle(self.random_past_years)

    def update_apy(self, year_index, fund: Fund):
        if self.use_historical_sp500:
            new_apy = self.sp500_by_year[self.random_past_years[year_index]]
        else:
            new_apy = self.default_apy
        if self.reduce_apy_by_inflation:
            new_apy -= self.inflation_by_year[self.random_past_years[year_index]]
        fund.set_apy(new_apy)

        if self.apply_inflation_to_contributions:
            fund.set_inflation_rate(self.inflation_by_year[self.random_past_years[year_index]])


class WealthVisualizer:
    def __init__(self):
        self.name = "Wealth Visualizer"
        self.colors = []

    def visualize_results(self, results: List[List[FundTransaction]]):
        fig1, ax1 = plt.subplots(sharex=True)
        ax2 = ax1.twinx()
        fig2, ax3 = plt.subplots(sharex=True)
        self.make_n_colors(len(results))
        color_index = 0
        first_date = None
        last_date = None

        for history in results:
            years = []
            balances = []
            balance_dates = []
            apy_values = []
            yearly_contrib = []
            for h in history:
                if h.type == FundTransactionType.BALANCE:
                    balance_dates.append(h.date)
                    years.append(h.date.year)
                    balances.append(h.amount)
                if h.type == FundTransactionType.APY:
                    apy_values.append(h.amount)
                if h.type == FundTransactionType.CONTRIBUTION_SUMMARY:
                    yearly_contrib.append(h.amount)

            assert(len(balances) == len(apy_values))
            first_date = balance_dates[0]
            last_date = balance_dates[len(balance_dates) - 1]

            ax1.bar(years, apy_values, color=self.colors[color_index], alpha=0.5)
            ax2.plot(years, balances, color=self.colors[color_index], label=f"Simulation {color_index}")

            ax3.plot(years, yearly_contrib, color=self.colors[color_index] )
            color_index += 1

        ax1.set_title(f"Balance from {first_date} " + f" to {last_date}")
        ax1.set_ylabel("Market APY")
        ax1.set_xlabel("Years")

        ax2.set_ylabel('Balance in $')
        ax2.set_xlabel("Years")
        ax2.legend()

        ax3.set_title("Contributions/Withdrawals")
        ax3.set_ylabel("Amount added/removed in $")
        ax3.set_xlabel("Years")
        plt.show()

    def make_n_colors(self, n: int):
        initial_color = (0.5, 0.0, 0.2)
        step_size = 1.0 / n

        self.colors = []
        for i in range(n):
            # Increment RGB values by the step size
            new_color = (
                (initial_color[0] + step_size * i) % 1.0,  # Red component
                (initial_color[1] + step_size * i) % 1.0,  # Green component
                (initial_color[2] + step_size * i) % 1.0  # Blue component
            )
            self.colors.append(new_color)

    @staticmethod
    def visualize_market_returns_distribution():
        # See https://papers.ssrn.com/sol3/papers.cfm?abstract_id=955639
        # Egan proposes a t-distribution for SP500 returns with nu=3.6 to widen the tails to
        # increase the likelihood of more extreme returns
        # Also see https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histretSP.html  for historical SP500
        scenario = RetirementScenario()
        returns = scenario.sp500_by_year.values()

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


if __name__ == '__main__':
    v = WealthVisualizer()
    s = RetirementScenario()
    s.run_scenario(seeds=[26, 27])
    v.visualize_results(s.results)
