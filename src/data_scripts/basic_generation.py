import csv
import numpy as np

num_transactions = 1000
min_transaction_amount = 10
max_transaction_amount = 20
num_banks = 5

banks = np.arange(num_banks)
banks_transactions = dict.fromkeys(banks, [])
timesteps = np.arange(num_transactions)

# Set random transactions equally distributed among all banks
num_bank_transactions = num_transactions//num_banks
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
random_data = [(timestep, ) + transaction for timestep, transaction in zip(timesteps, all_transactions)]


ordered_bank_transactions = []
for bank in banks_transactions:
    ordered_bank_transactions.append(banks_transactions[bank])

alternative_data = (np.array(ordered_bank_transactions)
                    .transpose(1, 0, 2)
                    .reshape(-1, np.array(ordered_bank_transactions).shape[2]))
alternative_data = np.column_stack((timesteps, alternative_data))

with (open('../data/synthetic_data/reactive/reactive_data.csv', 'w', newline='') as reactive,
      open('../data/synthetic_data/random/random_data.csv', 'w', newline='') as random,
      open('../data/synthetic_data/alternative/alternative_data.csv', 'w', newline='') as alternative):
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
