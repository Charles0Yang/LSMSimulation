import numpy as np
from scipy import integrate
from stable_baselines3 import PPO

from src.classes.configs.data_generation_config import DataGenerationConfig
from src.classes.transaction import DatedTransaction
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
        else:
            self.non_priority_balance -= transaction.amount
        self.update_total_balance()
        self.check_min_balance()

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


class NormalBank(AgentBank):
    def __init__(self, id, name, balance, input_file):
        super().__init__(id, name, balance, input_file)

    def check_for_transactions(self, time, metrics):
        while self.transactions_to_do and time == self.transactions_to_do[0].time:
            transaction = self.transactions_to_do.pop(0)
            metrics.add_transaction()
            self.total_transactions += 1
            if transaction.priority == 1:
                self.add_transaction_to_priority_queue(transaction)
            else:
                self.add_transaction_to_non_priority_queue(transaction)


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


class RLDelayBank(DelayBank):
    def __init__(self, id, name, balance, input_file, delay_amount):
        super().__init__(id, name, balance, input_file, int(delay_amount/2))
        self.model = PPO.load("/Users/cyang/PycharmProjects/PartIIProject/src/rl/models.zip")

    def calculate_delay_benefit(self, time, amount):
        obs = np.array([self.balance, amount, self.min_balance])
        action, _ = self.model.predict(obs)
        return int(action)


class DelayWhenConvenientBank(DelayBank):
    def __init__(self, id, name, balance, input_file, delay_amount):
        super().__init__(id, name, balance, input_file, delay_amount)
        self.extra_holding_queue = Queue()
        self.priority_balance = self.balance
        self.non_priority_balance = 0

    def check_for_transactions(self, time, metrics):
        while self.transactions_to_do and time == self.transactions_to_do[0].time:
            transaction = self.transactions_to_do.pop(0)
            self.total_transactions += 1
            metrics.add_transaction()
            print(
                f"{time}: Plan on transaction {transaction} with balance currently at {self.balance}, min balance is {self.min_balance}")
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
                print(
                    f"{time}: Delivering transaction {top_transaction}, balance before transaction is {balance_before_transaction}, balance after transaction is {temp_balance}")
                top_transaction.time = time
                top_transaction.priority = 1
                self.add_transaction_to_priority_queue(top_transaction)

                if not self.extra_holding_queue.empty():
                    top_transaction = list(self.extra_holding_queue.queue)[0]

        self.total_time_delay += self.extra_holding_queue.qsize()
        metrics.add_bank_delay(self.extra_holding_queue.qsize())

    def outbound_transaction(self, transaction: DatedTransaction):
        if transaction.priority == 1:
            if transaction.amount > self.priority_balance:
                self.non_priority_balance = self.non_priority_balance - (
                        transaction.amount - self.priority_balance)  # If transaction amount over priority balance then use up non-priority balance
                self.priority_balance = 0
            else:
                self.priority_balance -= transaction.amount
        else:
            self.non_priority_balance -= transaction.amount
        self.update_total_balance()
        self.check_min_balance()
        print(f"{transaction.time}: Sending {transaction}")
