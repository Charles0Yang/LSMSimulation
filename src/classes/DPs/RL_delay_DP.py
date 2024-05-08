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


class RLDelayBank(DelayBank):
    def __init__(self, id, name, balance, input_file, delay_amount):
        super().__init__(id, name, balance, input_file, int(delay_amount/2))
        self.model = PPO.load(f"/Users/cyang/PycharmProjects/PartIIProject/src/rl/delay_0.zip")
        self.delay_percentage = 0

    def calculate_delay_benefits(self, balance, amount, min_balance):
        obs = np.array([self.balance, amount, self.min_balance])
        action, _ = self.model.predict(obs)
        self.delay_percentage += action
        print(f"RL Bank Action is {action}")
        return int(action)


    def check_for_transactions(self, time, metrics):
        temp_balance = self.balance
        temp_min_balance = self.min_balance
        while self.transactions_to_do and time >= self.transactions_to_do[0].time:
            if self.calculate_delay_benefits(temp_balance, self.transactions_to_do[0].amount, temp_min_balance) == 0:
                transaction = self.transactions_to_do.pop(0)
                self.total_transactions += 1
                if time > transaction.time:
                    self.num_transactions_delayed += 1
                    self.total_time_delay += (time - transaction.time).total_seconds()
                metrics.add_transaction()
                transaction.time = time
                if transaction.priority == 1:
                    self.add_transaction_to_priority_queue(transaction)
                else:
                    self.add_transaction_to_non_priority_queue(transaction)
                temp_balance -= transaction.amount
                if temp_balance < temp_min_balance:
                    temp_min_balance = temp_balance
            else:
                transaction = self.transactions_to_do.pop(0)
                transaction.time += timedelta(seconds=settings.delay_amount)
                if transaction.time > settings.end_time:
                    transaction.time = settings.end_time
                for i in range(len(self.transactions_to_do)):
                    if transaction.time <= self.transactions_to_do[i].time:
                        self.transactions_to_do.insert(i, transaction)
                        break
                break