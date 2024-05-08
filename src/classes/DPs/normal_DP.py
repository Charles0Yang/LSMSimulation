import bisect

import numpy as np
from scipy import integrate
from stable_baselines3 import PPO

from src.classes.DPs.base_DP import AgentBank
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

class NormalBank(AgentBank):
    def __init__(self, id, name, balance, input_file):
        super().__init__(id, name, balance, input_file)

    def check_for_transactions(self, time, metrics):
        while self.transactions_to_do and time == self.transactions_to_do[0].time:
            transaction = self.transactions_to_do.pop(0)
            self.total_transactions += 1
            if transaction.priority == 1:
                self.add_transaction_to_priority_queue(transaction)
            else:
                self.add_transaction_to_non_priority_queue(transaction)