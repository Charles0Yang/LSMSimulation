from src.classes.bank import Bank
from src.classes.csv_settings import CSVSettings
from src.classes.day_config import DayConfig
from src.classes.transaction import Transaction
from src.matching import naive_bilateral_matching
from src.utils.csvutils import read_csv, write_to_csv

from queue import Queue


def generate_banks(num_banks, starting_balance):
    banks = {}
    bank_name = "A"
    for i in range(num_banks):
        banks[i] = Bank(i, bank_name, starting_balance)
        bank_name = chr(ord(bank_name) + 1)

    return banks


def fetch_all_bank_balances(banks):
    current_bank_balances = []
    for bank_id in banks:
        current_bank_balances.append(banks[bank_id].balance)

    return current_bank_balances


def read_transactions(file_name):
    rows = read_csv(file_name)
    transactions = []
    for row in rows:
        timestep = int(row[0])
        sending_bank_id = int(row[1])
        receiving_bank_id = int(row[2])
        amount = float(row[3])

        transaction = Transaction(timestep, sending_bank_id, receiving_bank_id, amount)
        transactions.append(transaction)

    return transactions


def simulate_day_transactions(day_config: DayConfig, csv_settings: CSVSettings):
    transactions = read_transactions(csv_settings.input_file_name)
    banks = generate_banks(day_config.num_banks, day_config.starting_balance)
    bank_balances = []
    timesteps = []

    transactionQueue = Queue()

    for transaction in transactions:
        if not day_config.LSM_enabled:
            banks[transaction.sending_bank_id].outbound_transaction(transaction)
            banks[transaction.receiving_bank_id].inbound_transaction(transaction)
        else:
            transactionQueue.put(transaction)
            if transaction.time % day_config.matching_window == day_config.matching_window - 1:
                naive_bilateral_matching(banks, transactionQueue, transaction.time)

        timesteps.append(transaction.time)
        current_bank_balances = fetch_all_bank_balances(banks)
        bank_balances.append(current_bank_balances)

    write_to_csv(csv_settings.output_file_name, csv_settings.headers, bank_balances)
