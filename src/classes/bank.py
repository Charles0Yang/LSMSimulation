from src.classes.configs.data_generation_config import DataGenerationConfig
from src.classes.transaction import DatedTransaction
from abc import ABC, abstractmethod
from datetime import datetime, timedelta


class Bank:
    # These numbers from recent Jan 2023 BoE paper changing the closing time from 4:20PM to 6:20PM
    opening_time = datetime(2023, 1, 1, 5, 45)
    closing_time = datetime(2023, 1, 1, 18, 20)

    def __init__(self, id, name, balance):
        self.id = id
        self.name = name
        self.balance = balance
        self.min_balance = 100000000
        self.transactions_completed = []
        self.transactions_to_do = []

    def inbound_transaction(self, transaction: DatedTransaction):
        self.balance += transaction.amount
        self.check_min_balance()

    def outbound_transaction(self, transaction: DatedTransaction):
        self.balance -= transaction.amount
        self.check_min_balance()

    def check_min_balance(self):
        if self.balance < self.min_balance:
            self.min_balance = self.balance


class AgentBank(ABC, Bank):
    def __int__(self, id, name, balance, transaction_distribution):
        super().__init__(id, name, balance)
        self.transaction_distribution = transaction_distribution

    @abstractmethod
    def generate_transactions(self):
        pass


class NormalBank(AgentBank):
    def __int__(self, id, name, balance, transaction_distribution):
        super().__init__(id, name, balance, transaction_distribution)

    def assign_time_to_transaction(self, current_time):
        pass



