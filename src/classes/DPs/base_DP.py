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


def convert_datetime_to_decimal(date):
    return date.hour + date.minute / 60.0


class Bank:
    def __init__(self, id, name, balance, input_file):
        self.id = id
        self.name = name
        self.balance = balance
        self.priority_balance = balance * settings.priority_balance_percentage
        self.non_priority_balance = balance * (1 - settings.priority_balance_percentage)
        self.transactions_completed = []
        self.transactions_to_do = self.get_transactions(input_file)
        self.priority_transaction_queue = []
        self.non_priority_transaction_queue = []
        self.opening_time = datetime(2023, 1, 1, 5, 45)
        self.closing_time = datetime(2023, 1, 1, 18, 20)
        self.min_balance = balance
        self.cum_settlement_delay = 0

    def inbound_transaction(self, transaction: DatedTransaction):
        if transaction.priority == 1:
            self.priority_balance += transaction.amount
        else:
            self.non_priority_balance += transaction.amount
        self.update_total_balance()

    def outbound_transaction(self, transaction: DatedTransaction):
        if transaction.priority == 1:
            if transaction.amount > self.priority_balance:
                self.non_priority_balance = self.non_priority_balance - (
                        transaction.amount - self.priority_balance)  # If transaction amount over priority balance then use up non-priority balance
                self.priority_balance = 0
            else:
                self.priority_balance -= transaction.amount
            #self.priority_balance -= transaction.amount
        else:
            self.non_priority_balance -= transaction.amount
        self.update_total_balance()
        #self.check_min_balance()

    def update_total_balance(self):
        self.balance = self.priority_balance + self.non_priority_balance

    def check_min_balance(self):
        if self.balance < self.min_balance:
            self.min_balance = self.balance

    def add_transaction_to_priority_queue(self, transaction):
        heapq.heappush(self.priority_transaction_queue, (transaction.time, transaction))

    def add_transaction_to_non_priority_queue(self, transaction):
        heapq.heappush(self.non_priority_transaction_queue, (transaction.time, transaction))

    def pop_transaction_from_priority_queue(self):
        date, transaction = heapq.heappop(self.priority_transaction_queue)
        return transaction

    def pop_transaction_from_non_priority_queue(self):
        date, transaction = heapq.heappop(self.non_priority_transaction_queue)
        return transaction

    def post_transactions(self, time):
        transactions_to_post = []

        while len(self.priority_transaction_queue) != 0 and time == self.priority_transaction_queue[0][1].time:
            transaction = self.pop_transaction_from_priority_queue()
            transactions_to_post.append(transaction)

        while len(self.non_priority_transaction_queue) != 0 and time == self.non_priority_transaction_queue[0][1].time:
            transaction = self.pop_transaction_from_non_priority_queue()
            transactions_to_post.append(transaction)

        return transactions_to_post

    def get_transactions(self, file_name):
        df = pd.read_csv(f"/Users/cyang/PycharmProjects/PartIIProject/data/synthetic_data/{file_name}")
        transactions_to_do = df[df['from'] == self.id].iloc[0:].values.tolist()
        transactions = []
        for row in transactions_to_do:
            time = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
            sending_bank_id = int(row[1])
            receiving_bank_id = int(row[2])
            amount = float(row[3])
            priority = int(row[4])

            transaction = DatedTransaction(sending_bank_id, receiving_bank_id, amount, time, priority)
            transactions.append(transaction)

        return transactions


class AgentBank(ABC, Bank):
    def __init__(self, id, name, balance, input_file):
        super().__init__(id, name, balance, input_file)
        self.total_time_delay = 0  # seconds
        self.total_transactions = 0

    def add_delay(self):
        self.total_time_delay += 1

    def calculate_average_delay_per_transaction(self):
        if self.total_transactions == 0:
            return 0
        return (self.total_time_delay / 60) / self.total_transactions  # minutes

    @abstractmethod
    def check_for_transactions(self, time, metrics):
        pass