from src.classes.configs.data_generation_config import DataGenerationConfig
from src.classes.transaction import DatedTransaction
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import pandas as pd
from queue import Queue


class Bank:
    def __init__(self, id, name, balance, input_file):
        self.id = id
        self.name = name
        self.balance = balance
        self.transactions_completed = []
        self.transactions_to_do = self.get_transactions(input_file)
        self.transaction_queue = Queue()
        self.opening_time = datetime(2023, 1, 1, 5, 45)
        self.closing_time = datetime(2023, 1, 1, 18, 20)
        self.min_balance = 100000000
        self.cum_settlement_delay = 0

    def inbound_transaction(self, transaction: DatedTransaction):
        self.balance += transaction.amount
        self.check_min_balance()

    def outbound_transaction(self, transaction: DatedTransaction):
        self.balance -= transaction.amount
        self.check_min_balance()

    def check_min_balance(self):
        if self.balance < self.min_balance:
            self.min_balance = self.balance

    def add_transaction_to_queue(self, transaction):
        self.transaction_queue.put(transaction)

    def pop_transaction_from_queue(self):
        return self.transaction_queue.get()

    def post_transactions(self, time):
        transactions_to_post = []
        while not self.transaction_queue.empty() and time == self.transaction_queue.queue[0].time:
            transaction = self.pop_transaction_from_queue()
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

            transaction = DatedTransaction(sending_bank_id, receiving_bank_id, amount, time)
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
            self.add_transaction_to_queue(self.transactions_to_do.pop(0))



class DelayBank(AgentBank):
    def __init__(self, id, name, balance, input_file, delay_amount):
        super().__init__(id, name, balance, input_file)
        self.delay_amount = delay_amount

    # Checks for transactions they need to do then delays and puts them into a separate queue
    def check_for_transactions(self, time):
        while self.transactions_to_do and time == self.transactions_to_do[0].time:
            transaction = self.transactions_to_do.pop(0)
            transaction.time += timedelta(seconds=self.delay_amount)
            self.cum_settlement_delay += self.delay_amount
            if transaction.time > self.closing_time:
                transaction.time = self.closing_time
            self.add_transaction_to_queue(transaction)
