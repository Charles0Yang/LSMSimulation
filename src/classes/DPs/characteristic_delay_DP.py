import bisect

import numpy as np
from scipy import integrate
from stable_baselines3 import PPO

from src.classes.DPs.base_DP import AgentBank
from src.classes.DPs.base_delay_DP import DelayBank
from src.classes.configs.data_generation_config import DataGenerationConfig
from src.classes.payment import DatedTransaction
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import pandas as pd
import heapq
from queue import Queue
from scipy.stats import norm, gaussian_kde

from src.simulation import settings
from src.simulation.settings import data_generation_config


class RuleBasedDelayBank(DelayBank):
    def __init__(self, id, name, balance, input_file, max_delay_amount):
        super().__init__(id, name, balance, input_file, max_delay_amount)
        self.timing_delay_kde = self.generate_timing_delay_pdf()[0]
        self.timing_delay_max_pdf = self.generate_timing_delay_pdf()[1]
        self.amount_delay_pdf = self.generate_transaction_amount_delay_pdf()[0]
        self.amount_x_values = self.generate_transaction_amount_delay_pdf()[1]

    def generate_timing_delay_pdf(self):
        peak1_params = {'mean': 7, 'std_dev': 2}
        peak2_params = {'mean': 14, 'std_dev': 1.5}
        size = 1000

        peak1_distribution = norm.rvs(loc=peak1_params['mean'], scale=peak1_params['std_dev'], size=size)
        peak2_distribution = norm.rvs(loc=peak2_params['mean'], scale=peak2_params['std_dev'], size=int(size / 2))

        combined_distribution = np.concatenate([peak1_distribution, peak2_distribution])

        bandwidth = 0.5
        kde = gaussian_kde(combined_distribution, bw_method=bandwidth)

        lower_limit = convert_datetime_to_decimal(settings.start_time)
        upper_limit = convert_datetime_to_decimal(settings.end_time)

        peak_x_value = np.linspace(lower_limit, upper_limit, 10000)
        peak_x_value_at_max = max(kde(peak_x_value))

        # timing_probability = kde.evaluate([convert_datetime_to_decimal(time)])[0] / peak_x_value_at_max
        return kde, peak_x_value_at_max

    def generate_transaction_amount_delay_pdf(self):
        alpha = 2
        x_values = np.linspace(data_generation_config.min_transaction_amount,
                               data_generation_config.max_transaction_amount, 1000)
        pdf_values = np.log(x_values) ** alpha / max(np.log(x_values)) ** alpha
        return pdf_values, x_values

    def calculate_timing_delay_prob(self, time):
        return self.timing_delay_kde.evaluate([convert_datetime_to_decimal(time)])[0] / self.timing_delay_max_pdf

    def calculate_transaction_delay_weight(self, amount):
        return np.interp(amount, self.amount_x_values, self.amount_delay_pdf)

    def calculate_delay_benefit(self, time, amount):
        return self.calculate_timing_delay_prob(time) * self.calculate_transaction_delay_weight(amount)
