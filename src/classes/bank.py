from src.classes.configs.data_generation_config import DataGenerationConfig
from src.classes.transaction import DatedTransaction
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import pandas as pd
from queue import Queue

from src.simulation import settings


class Bank:
    def __init__(self, id, name, balance, input_file):
        self.id = id
        self.name = name
        self.balance = balance
        self.priority_balance = balance * settings.priority_balance_percentage
        self.non_priority_balance = balance * (1-settings.priority_balance_percentage)
        self.transactions_completed = []
        self.transactions_to_do = self.get_transactions(input_file)
        self.priority_transaction_queue = Queue()
        self.non_priority_transaction_queue = Queue()
        self.opening_time = datetime(2023, 1, 1, 5, 45)
        self.closing_time = datetime(2023, 1, 1, 18, 20)
        self.min_balance = 100000000
        self.cum_settlement_delay = 0

    def inbound_transaction(self, transaction: DatedTransaction):
        if transaction.priority == 1:
            self.priority_balance += transaction.amount
        else:
            self.non_priority_balance += transaction.amount
        self.check_min_balance()
        self.update_total_balance()

    def outbound_transaction(self, transaction: DatedTransaction):
        if transaction.priority == 1:
            if transaction.amount > self.priority_balance:
                self.non_priority_balance = self.non_priority_balance - (transaction.amount - self.priority_balance)  # If transaction amount over priority balance then use up non-priority balance
                self.priority_balance = 0
            else:
                self.priority_balance -= transaction.amount
        else:
            self.non_priority_balance -= transaction.amount
        self.check_min_balance()
        self.update_total_balance()

    def update_total_balance(self):
        self.balance = self.priority_balance + self.non_priority_balance

    def check_min_balance(self):
        if self.balance < self.min_balance:
            self.min_balance = self.balance

    def add_transaction_to_priority_queue(self, transaction):
        self.priority_transaction_queue.put(transaction)

    def add_transaction_to_non_priority_queue(self, transaction):
        self.non_priority_transaction_queue.put(transaction)

    def pop_transaction_from_priority_queue(self):
        return self.priority_transaction_queue.get()

    def pop_transaction_from_non_priority_queue(self):
        return self.non_priority_transaction_queue.get()

    def post_transactions(self, time):
        transactions_to_post = []

        while not self.priority_transaction_queue.empty() and time == self.priority_transaction_queue.queue[0].time:
            transaction = self.pop_transaction_from_priority_queue()
            transactions_to_post.append(transaction)

        while not self.non_priority_transaction_queue.empty() and time == self.non_priority_transaction_queue.queue[0].time:
            transaction = self.pop_transaction_from_non_priority_queue()
            transactions_to_post.append(transaction)

        return transactions_to_post

    def get_transactions(self, file_name):
        df = pd.read_csv(f"/Users/cyang/PycharmProjects/PartIIProject/data/synthetic_data/{file_name}")
        transactions_to_do = df[df['from'] == self.id].iloc[1:].values.tolist()
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
    def __int__(self, id, name, balance, input_file, delay_amount):
        super().__init__(id, name, balance)
        self.delay_amount = delay_amount

    @abstractmethod
    def check_for_transactions(self, time):
        pass


class NormalBank(AgentBank):
    def __init__(self, id, name, balance, input_file):
        super().__init__(id, name, balance, input_file)

    def check_for_transactions(self, time):
        while self.transactions_to_do and time == self.transactions_to_do[0].time:
            transaction = self.transactions_to_do.pop(0)
            if transaction.priority == 1:
                self.add_transaction_to_priority_queue(transaction)
            else:
                self.add_transaction_to_non_priority_queue(transaction)


class DelayBank(AgentBank):
    def __init__(self, id, name, balance, input_file, delay_amount):
        super().__init__(id, name, balance, input_file)
        self.delay_amount = delay_amount

    # Checks for transactions they need to do, then delay and puts them into a separate queue
    def check_for_transactions(self, time):
        while self.transactions_to_do and time == self.transactions_to_do[0].time:
            transaction = self.transactions_to_do.pop(0)
            transaction.time += timedelta(seconds=self.delay_amount)
            self.cum_settlement_delay += self.delay_amount
            if transaction.time > self.closing_time:
                transaction.time = self.closing_time
            if transaction.priority == 1:
                self.add_transaction_to_priority_queue(transaction)
            else:
                self.add_transaction_to_non_priority_queue(transaction)