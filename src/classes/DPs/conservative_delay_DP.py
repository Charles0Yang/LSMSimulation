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


class DelayWhenConvenientBank(DelayBank):
    def __init__(self, id, name, balance, input_file, delay_amount):
        super().__init__(id, name, balance, input_file, delay_amount)
        self.extra_holding_queue = Queue()
        self.priority_balance = self.balance
        self.non_priority_balance = 0

    def checks_for_transactions(self, time, metrics):
        while self.transactions_to_do and time == self.transactions_to_do[0].time:
            transaction = self.transactions_to_do.pop(0)
            self.total_transactions += 1
            metrics.add_transaction()
            self.extra_holding_queue.put(transaction)

        if not self.extra_holding_queue.empty():
            top_transaction = list(self.extra_holding_queue.queue)[0]
            temp_balance = self.balance
            temp_min_balance = self.min_balance
            while not self.extra_holding_queue.empty() and temp_balance - top_transaction.amount >= temp_min_balance:
                top_transaction = self.extra_holding_queue.get()
                balance_before_transaction = temp_balance
                temp_balance = temp_balance - top_transaction.amount
                if temp_balance < temp_min_balance:
                    temp_min_balance = temp_balance
                if top_transaction.time != time:
                    self.num_transactions_delayed += 1
                top_transaction.time = time
                top_transaction.priority = 1
                self.add_transaction_to_priority_queue(top_transaction)

                if not self.extra_holding_queue.empty():
                    top_transaction = list(self.extra_holding_queue.queue)[0]

        self.total_time_delay += self.extra_holding_queue.qsize()
        metrics.add_bank_delay(self.extra_holding_queue.qsize())

    def check_for_transactions(self, time, metrics):
        temp_balance = self.balance
        while self.transactions_to_do and time >= self.transactions_to_do[0].time:
            if temp_balance - self.transactions_to_do[0].amount >= self.min_balance:
                transaction = self.transactions_to_do.pop(0)
                self.total_transactions += 1
                if time > transaction.time:
                    self.num_transactions_delayed += 1
                    self.total_time_delay += (time - transaction.time).total_seconds()
                metrics.add_transaction()
                transaction.time = time
                transaction.priority = 1
                self.add_transaction_to_priority_queue(transaction)
                temp_balance -= transaction.amount
            else:
                break