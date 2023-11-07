import csv
from datetime import datetime, timedelta
import numpy as np


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

    transaction_times = np.random.uniform(0, (end_time - start_time).seconds // 60, size=data_generation_config.num_transactions)
    timesteps = np.array(sorted([start_time + timedelta(minutes=int(time)) for time in transaction_times]))

    # Set random transactions equally distributed among all banks
    num_bank_transactions = num_transactions // num_banks
    for bank in banks:
        amounts = np.random.randint(min_transaction_amount,
                                    max_transaction_amount,
                                    num_bank_transactions)
        from_banks = np.ones(num_bank_transactions, dtype=int) * bank
        to_banks = np.random.choice(np.delete(banks, bank), num_bank_transactions)
        banks_transactions[bank] = list(zip(from_banks, to_banks, amounts))

    all_transactions = []
    for bank in banks_transactions:
        for transactions in banks_transactions[bank]:
            all_transactions.append(transactions)

    reactive_data = [(timestep,) + transaction for timestep, transaction in zip(timesteps, all_transactions)]

    np.random.shuffle(all_transactions)
    random_data = [(str(timestep),) + transaction for timestep, transaction in zip(timesteps, all_transactions)]

    ordered_bank_transactions = []
    for bank in banks_transactions:
        ordered_bank_transactions.append(banks_transactions[bank])

    alternative_data = (np.array(ordered_bank_transactions)
                        .transpose(1, 0, 2)
                        .reshape(-1, np.array(ordered_bank_transactions).shape[2]))
    alternative_data = np.column_stack((timesteps, alternative_data))

    with (open('/Users/cyang/PycharmProjects/PartIIProject/src/data/synthetic_data/reactive/reactive_data.csv', 'w', newline='') as reactive,
          open('/Users/cyang/PycharmProjects/PartIIProject/src/data/synthetic_data/random/random_data.csv', 'w', newline='') as random,
          open('/Users/cyang/PycharmProjects/PartIIProject/src/data/synthetic_data/alternative/alternative_data.csv', 'w', newline='') as alternative):
        reactive_writer = csv.writer(reactive, delimiter=',')
        random_writer = csv.writer(random, delimiter=',')
        alternative_writer = csv.writer(alternative, delimiter=',')

        reactive_writer.writerow(["time", "to", "from", "amount"])
        random_writer.writerow(["time", "to", "from", "amount"])
        alternative_writer.writerow(["time", "to", "from", "amount"])

        for row in reactive_data:
            reactive_writer.writerow(row)

        for row in random_data:
            random_writer.writerow(row)

        for row in alternative_data:
            alternative_writer.writerow(row)
