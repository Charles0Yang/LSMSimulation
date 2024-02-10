import csv
from datetime import datetime, timedelta
import numpy as np
from scipy.stats import gaussian_kde

from src.classes.configs.data_generation_config import DataGenerationConfig
from src.simulation import settings


def convert_seconds_to_datetime(seconds):
    hours = seconds // 3600
    remaining_seconds = seconds % 3600
    minutes = remaining_seconds // 60
    seconds = remaining_seconds % 60
    return datetime(2023, 1, 1, hours, minutes, seconds)


def generate_characteristic_times(num_transactions):
    # Generate synthetic data for demonstration in seconds since datetime(2023, 1, 1, 0, 0, 0)
    np.random.seed(42)
    data = np.concatenate([
        np.random.normal(6 * 3600, 3600, 500),  # increasing transactions between 6-8
        np.random.normal(8 * 3600, 3600, 500),  # decreasing transactions until 12
        np.random.normal(15 * 3600, 3600, 500),  # increasing transactions until 3
        np.random.normal(18 * 3600, 3600, 500),  # decreasing transactions until 6:20 pm
    ])

    kde = gaussian_kde(data, bw_method=0.5)
    valid_range = (20700, 66000) # in seconds from the start of the day (e.g. 20700 is 5:45am and 66000 is 6:20pm)
    transaction_times_seconds = []

    while len(transaction_times_seconds) < num_transactions:
        random_samples = kde.resample(num_transactions - len(transaction_times_seconds))[0]
        valid_samples = [sample for sample in random_samples if valid_range[0] <= sample <= valid_range[1]]
        transaction_times_seconds.extend(valid_samples)

    transaction_times_seconds = transaction_times_seconds[:num_transactions]
    transaction_times_seconds.sort()
    times = []
    for time in transaction_times_seconds:
        times.append(convert_seconds_to_datetime(int(time)))

    return times


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

    transaction_times = np.random.uniform(0, (end_time - start_time).seconds,
                                          size=data_generation_config.num_transactions)
    #timesteps = np.array(sorted([start_time + timedelta(seconds=int(time)) for time in transaction_times]))
    timesteps = np.array(generate_characteristic_times(num_transactions))
    priorities = (np.random.random(size=len(transaction_times)) > settings.priority_transaction_percentage).astype(int)

    # Set random transactions equally distributed among all banks
    num_bank_transactions = num_transactions // num_banks
    for bank in banks:
        amounts = np.clip(np.round(np.random.normal(30, 20, size=num_bank_transactions)),
                          data_generation_config.min_transaction_amount,
                          data_generation_config.max_transaction_amount).astype(int)
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

    with (open('/Users/cyang/PycharmProjects/PartIIProject/data/synthetic_data/reactive/reactive_data.csv', 'w',
               newline='') as reactive,
          open('/Users/cyang/PycharmProjects/PartIIProject/data/synthetic_data/random/random_data.csv', 'w',
               newline='') as random,
          open('/Users/cyang/PycharmProjects/PartIIProject/data/synthetic_data/alternative/alternative_data.csv', 'w',
               newline='') as alternative):
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


"""
data_generation_config = DataGenerationConfig(
    num_banks=2,
    num_transactions=4000,
    min_transaction_amount=5,
    max_transaction_amount=20
)

generate_data(data_generation_config)
"""
