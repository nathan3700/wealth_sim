from datetime import date, timedelta
from wealth_fund import Fund, FundTransactionType, FundTransaction
from transfer_schedule import Frequency
import csv
from scipy.stats import t, norm
import matplotlib.pyplot as plt
import numpy as np
import random
from math import ceil
from typing import List, ForwardRef
RetirementScenarioRef = ForwardRef('RetirementScenario')


class RetirementScenario:
    class Run:
        def __init__(self, scenario: RetirementScenarioRef, name: str, seed: int, results: List[FundTransaction]):
            self.name = name
            self.results = results
            self.scenario: scenario
            self.seed = seed
            self.color_index = 0

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
        self.keep_historical_sp500_sequence = True
        # Outputs
        self.runs: List[RetirementScenario.Run] = []

        # State
        self.sp500_by_year = dict()
        self.inflation_by_year = dict()
        self.past_years = []
        self.random_past_years = []
        self.random_year_index = 0
        self.random_start_years_used = set()
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
            self.randomize_history(seed)
            if self.use_historical_sp500:
                if self.keep_historical_sp500_sequence:
                    name = f"Start History {self.past_years[self.random_year_index]}"
                else:
                    name = f"Shuffled Years Seed {seed}"
            else:
                name = f"?"
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
            run = RetirementScenario.Run(self, name, seed, fund.history)
            self.runs.append(run)

    def randomize_history(self, seed: int):
        random.seed(seed)
        if self.keep_historical_sp500_sequence:
            tries_left = 5
            while self.random_year_index in self.random_start_years_used and tries_left > 0:
                self.random_year_index = random.randint(0, len(self.past_years) - 1)
                tries_left -= 1
            self.random_start_years_used.add(self.random_year_index)
        else:
            self.random_past_years = [y for y in self.past_years]  # Duplicate
            random.shuffle(self.random_past_years)

    def update_apy(self, year_index, fund: Fund):
        historical_year = self.pick_new_historical_year(year_index)

        if self.use_historical_sp500:
            new_apy = self.sp500_by_year[historical_year]
        else:
            new_apy = self.default_apy
        if self.reduce_apy_by_inflation:
            new_apy -= self.inflation_by_year[historical_year]
        fund.set_apy(new_apy)

        if self.apply_inflation_to_contributions:
            fund.set_inflation_rate(self.inflation_by_year[historical_year])

    def pick_new_historical_year(self, year_index):
        if self.keep_historical_sp500_sequence:
            self.random_year_index += 1
            if self.random_year_index >= len(self.past_years):
                self.random_year_index = 0
            year = self.past_years[self.random_year_index]
        else:
            year = self.random_past_years[year_index]
        return year


class WealthVisualizer:
    def __init__(self):
        self.name = "Wealth Visualizer"
        self.colors = []
        self.line_styles = []
        self.worst_balance = None
        self.worst_run = RetirementScenario.Run(None, "", 0, [])
        self.best_balance = 0.0
        self.best_run = RetirementScenario.Run(None, "", 0, [])

    def visualize_results(self, runs: List[RetirementScenario.Run]):
        fig1, fig1_axes = plt.subplots(1, 2, figsize=(12, 5))
        ax_balances = fig1_axes[0]
        ax_transfers = fig1_axes[1]
        fig2, fig2_axes = plt.subplots(1, 2, figsize=(12, 5))
        ax_worst_apys = fig2_axes[0]
        ax_worst_run = ax_worst_apys.twinx()
        ax_best_apys = fig2_axes[1]
        ax_best_run = ax_best_apys.twinx()
        self.make_n_colors(len(runs))
        color_index = 0
        first_date = None
        last_date = None

        for run in runs:
            apy_values, balance_dates, balances, yearly_contrib, years = self.extract_history(run)
            first_date = balance_dates[0]
            highest_index = len(balance_dates) - 1
            last_date = balance_dates[highest_index]

            run.color_index = color_index
            ax_balances.plot(years, balances, color=self.colors[color_index], linestyle=self.line_styles[color_index], label=run.name)
            ax_transfers.plot(years, yearly_contrib, linestyle=self.line_styles[color_index], color=self.colors[color_index])
            color_index += 1

        date_range_str = f"Balance from {first_date} " + f" to {last_date}"
        ax_balances.set_title(date_range_str)
        ax_balances.set_ylabel('Balance in M$')
        ax_balances.yaxis.set_major_formatter(self.millions_formatter)
        ax_balances.set_xlabel("Years")
        ax_balances.legend()

        ax_transfers.set_title("Annual Contributions/Withdrawals")
        ax_transfers.set_ylabel("Yearly Transfers In(+)/Out(-) K$ (Thousands)")
        ax_transfers.yaxis.set_major_formatter(self.thousands_formatter)
        ax_transfers.set_xlabel("Years")

        self.plot_single_results(ax_worst_apys, ax_worst_run, "Worst", self.worst_run)
        self.plot_single_results(ax_best_apys, ax_best_run, "Best", self.best_run)
        fig2.tight_layout(pad=3.0)


    def plot_single_results(self, apy_axes, balances_axes, kind_of_performance, run):
        apy_values, balance_dates, balances, yearly_contrib, years = self.extract_history(run)
        balances_axes.set_title(f"{kind_of_performance} Performance ({run.name})")
        balances_axes.plot(years, balances, color=self.colors[run.color_index], linestyle=self.line_styles[run.color_index], label=run.name)
        # balances_axes.plot(years, yearly_contrib, color='black', label=f"Transfers")
        balances_axes.set_ylabel('Balance in K$')
        balances_axes.yaxis.set_major_formatter(self.millions_formatter)
        balances_axes.legend()
        apy_axes.bar(years, apy_values, color="green", alpha=0.5, label="APY")
        apy_axes.bar(years, self.extract_inflation(run), color="black", alpha=0.5, label="Inflation")
        apy_axes.set_ylabel('Percent Change (%)')
        apy_axes.legend()

    def extract_history(self, run: RetirementScenario.Run):
        years = []
        balances = []
        balance_dates = []
        apy_values = []
        yearly_contrib = []
        for h in run.results:
            if h.type == FundTransactionType.BALANCE:
                balance_dates.append(h.date)
                years.append(h.date.year)
                balances.append(h.amount)
            if h.type == FundTransactionType.APY:
                apy_values.append(h.amount)
            if h.type == FundTransactionType.CONTRIBUTION_SUMMARY:
                yearly_contrib.append(h.amount)

        assert(len(balances) == len(apy_values))
        assert(len(balances) == len(years))

        highest_index = len(balance_dates) - 1
        if balances[highest_index] > self.best_balance:
            self.best_balance = balances[highest_index]
            self.best_run = run
        if (self.worst_balance is None) or (balances[highest_index] < self.worst_balance):
            self.worst_balance = balances[highest_index]
            self.worst_run = run
        return apy_values, balance_dates, balances, yearly_contrib, years

    @staticmethod
    def extract_inflation(run: RetirementScenario.Run):
        inflation_history = []
        for h in run.results:
            if h.type == FundTransactionType.INFLATION:
                inflation_history.append(h.amount)
        return inflation_history

    def make_n_colors(self, n: int):
        step_size = 1.90 / ceil(n / 3)  # fractions of two colors per primary color (less than 2 to stay less white)
        line_styles = ['-', '--']
        rotate_line_style = 0
        current_dominant_color = 0  # Start on red
        steps_at_color = [ceil(n / 3), ceil(n / 3), ceil(n / 3)]
        color = [1.0, 0.0, 0.0]  # Start dominant red
        self.colors = []
        ping_pong = 0
        for i in range(n):
            # Ensure we didn't pick white
            if (round(color[0] * 10), round(color[1] * 10), round(color[2] * 10)) != (10, 10, 10):
                self.colors.append((color[0], color[1], color[2]))
            else:
                raise(Exception(f"Unable to create non-white color on iteration {i} colors color={color}"))

            color[(current_dominant_color + 1 + ping_pong) % 3] = (color[(current_dominant_color + 1 + ping_pong) % 3] + step_size)
            if color[(current_dominant_color + 1 + ping_pong) % 3] > 0.99:
                color[(current_dominant_color + 1 + ping_pong) % 3] = 1.0
                ping_pong = (ping_pong + 1) % 2
            steps_at_color[current_dominant_color] -= 1
            if steps_at_color[current_dominant_color] == 0:
                color = [0.0, 0.0, 0.0]
                current_dominant_color = (current_dominant_color + 1) % 3
                color[current_dominant_color] = 1.0
                ping_pong = (ping_pong + 1) % 2

            self.line_styles.append(line_styles[rotate_line_style])
            rotate_line_style = (rotate_line_style + 1) % (len(line_styles))


    @staticmethod
    def millions_formatter(x, pos):
        return f'{x / 1e6:.1f}M'  # Formats numbers in millions

    @staticmethod
    def thousands_formatter(x, pos):
        return f'{x / 1e3:.1f}K'

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
        fig, fig_axes = plt.subplots(1, 1)
        axes = fig_axes
        axes.hist(returns, bins=25, density=True, alpha=0.5, color='green', edgecolor='black')

        # Plotting the probability density function
        x = np.linspace(-100, 100, 1000)
        axes.plot(x, t.pdf(x, df=degrees_of_freedom, loc=location, scale=scale), 'r-', lw=2, label='PDF T-dist')
        axes.plot(x, norm.pdf(x, loc=location, scale=scale), 'black', lw=2, label='PDF Norm')

        axes.set_xlabel('Value')
        axes.set_ylabel('Density')
        axes.set_title('SP500 Returns against normal and t-distribution curves')
        axes.legend()

    @staticmethod
    def create_windows():
        plt.show()


if __name__ == '__main__':
    v = WealthVisualizer()
    s = RetirementScenario()
    s.run_scenario(seeds=[26, 27, 28, 29, 2342, 242, 999, 24442, 341, 1001, 1, 2, 3])
    v.visualize_results(s.runs)
    v.visualize_market_returns_distribution()
    v.create_windows()
