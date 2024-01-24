import csv
from datetime import datetime, timedelta
import numpy as np

from src.classes.configs.data_generation_config import DataGenerationConfig
from src.simulation import settings


def generate_data(data_generation_config):

    num_banks = data_generation_config.num_banks
    num_transactions = data_generation_config.num_transactions
    min_transaction_amount = data_generation_config.min_transaction_amount
    max_transaction_amount = data_generation_config.max_transaction_amount

    banks = np.arange(num_banks)
    banks_transactions = dict.fromkeys(banks, [])

    # Set the time range from 5:45 AM to 6:20 PM
    start_time = datetime(2023, 1, 1, 5, 45)  # 5:45 AM
    end_time = datetime(2023, 1, 1, 18, 20)  # 6:20 PM

    transaction_times = np.random.uniform(0, (end_time - start_time).seconds, size=data_generation_config.num_transactions)
    timesteps = np.array(sorted([start_time + timedelta(seconds=int(time)) for time in transaction_times]))
    priorities = (np.random.random(size=len(transaction_times)) > settings.priority_transaction_percentage).astype(int)

    # Set random transactions equally distributed among all banks
    num_bank_transactions = num_transactions // num_banks
    for bank in banks:
        amounts = np.clip(np.round(np.random.normal(30, 20, size=num_bank_transactions)), data_generation_config.min_transaction_amount, data_generation_config.max_transaction_amount).astype(int)
        from_banks = np.ones(num_bank_transactions, dtype=int) * bank
        to_banks = np.random.choice(np.delete(banks, bank), num_bank_transactions)
        banks_transactions[bank] = list(zip(from_banks, to_banks, amounts))

    all_transactions = []
    for bank in banks_transactions:
        for transactions in banks_transactions[bank]:
            all_transactions.append(transactions)

    reactive_data = [(timestep,) + transaction for timestep, transaction in zip(timesteps, all_transactions)]
    reactive_data = np.column_stack((reactive_data, priorities))

    np.random.shuffle(all_transactions)
    random_data = [(str(timestep),) + transaction for timestep, transaction in zip(timesteps, all_transactions)]
    random_data = np.column_stack((random_data, priorities))

    ordered_bank_transactions = []
    for bank in banks_transactions:
        ordered_bank_transactions.append(banks_transactions[bank])

    alternative_data = (np.array(ordered_bank_transactions)
                        .transpose(1, 0, 2)
                        .reshape(-1, np.array(ordered_bank_transactions).shape[2]))
    alternative_data = np.column_stack((timesteps, alternative_data, priorities))

    with (open('/Users/cyang/PycharmProjects/PartIIProject/data/synthetic_data/rl/reactive_data.csv', 'w', newline='') as reactive,
          open('/Users/cyang/PycharmProjects/PartIIProject/data/synthetic_data/rl/random_data.csv', 'w', newline='') as random,
          open('/Users/cyang/PycharmProjects/PartIIProject/data/synthetic_data/rl/alternative_data.csv', 'w', newline='') as alternative):
        reactive_writer = csv.writer(reactive, delimiter=',')
        random_writer = csv.writer(random, delimiter=',')
        alternative_writer = csv.writer(alternative, delimiter=',')

        reactive_writer.writerow(["time", "from", "to", "amount", "priority"])
        random_writer.writerow(["time", "from", "to", "amount", "priority"])
        alternative_writer.writerow(["time", "from", "to", "amount", "priority"])

        for row in reactive_data:
            reactive_writer.writerow(row)

        for row in random_data:
            random_writer.writerow(row)

        for row in alternative_data:
            alternative_writer.writerow(row)


data_generation_config = DataGenerationConfig(
    num_banks=2,
    num_transactions=4000,
    min_transaction_amount=5,
    max_transaction_amount=20
)

generate_data(data_generation_config)