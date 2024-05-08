from src.classes.DPs.base_DP import AgentBank
import bisect

import numpy as np
from scipy import integrate
from stable_baselines3 import PPO

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

class DelayBank(AgentBank):
    def __init__(self, id, name, balance, input_file, max_delay_amount):
        super().__init__(id, name, balance, input_file)
        self.max_delay_amount = max_delay_amount
        self.num_transactions_delayed = 0

    def calculate_percentage_transactions_delayed(self):
        if self.total_transactions == 0:
            return 0
        return self.num_transactions_delayed / self.total_transactions

    def check_for_transactions(self, time, metrics):
        while self.transactions_to_do and time == self.transactions_to_do[0].time:
            transaction = self.transactions_to_do.pop(0)
            delay_benefit = self.calculate_delay_benefit(transaction.time, transaction.amount)
            actual_delay = 0
            if delay_benefit > 0.5:
                actual_delay = int(self.max_delay_amount * (delay_benefit - 0.5) * 2)
                transaction.time += timedelta(seconds=actual_delay)
                self.num_transactions_delayed += 1
                self.total_time_delay += actual_delay
                metrics.add_bank_delay(actual_delay)
            self.total_transactions += 1
            self.cum_settlement_delay += actual_delay
            if transaction.time > self.closing_time:
                transaction.time = self.closing_time
            metrics.add_transaction()
            if transaction.priority == 1:
                self.add_transaction_to_priority_queue(transaction)
            else:
                self.add_transaction_to_non_priority_queue(transaction)

    def calculate_delay_benefit(self, time, amount):
        pass