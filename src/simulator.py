from datetime import datetime, timedelta

from src.classes.bank import Bank, NormalBank, DelayBank
from src.classes.configs.csv_config import CSVSettings
from src.classes.configs.day_config import DayConfig
from src.classes.transaction import DatedTransaction
from src.matching import Matching
from src.utils.csvutils import read_csv, write_to_csv


def generate_banks(num_banks, starting_balance, input_file):
    banks = {}
    bank_name = "A"
    for i in range(num_banks):
        if i % 2 == 0:
            banks[i] = NormalBank(i, bank_name, starting_balance, input_file)
        else:
            banks[i] = DelayBank(i, bank_name, starting_balance, input_file, 0)
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
        time = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
        sending_bank_id = int(row[1])
        receiving_bank_id = int(row[2])
        amount = float(row[3])

        transaction = DatedTransaction(sending_bank_id, receiving_bank_id, amount, time)
        transactions.append(transaction)

    return transactions


def simulate_day_transactions(day_config: DayConfig, csv_settings: CSVSettings):
    start_time = datetime(2023, 1, 1, 5, 45)
    end_time = datetime(2023, 1, 1, 18, 20)

    transactions = read_transactions(csv_settings.input_file_name)
    banks = generate_banks(day_config.num_banks, day_config.starting_balance, csv_settings.input_file_name)
    bank_balances = []

    current_time = start_time
    while current_time != end_time :

        transactions_to_execute = []
        for bank in banks:
            banks[bank].check_and_add_transaction(current_time)
            bank_transactions = banks[bank].execute_transaction_from_queue(current_time)
            for transaction in bank_transactions:
                transactions_to_execute.append(transaction)

        for transaction in transactions_to_execute:
            banks[transaction.sending_bank_id].outbound_transaction(transaction)
            banks[transaction.receiving_bank_id].inbound_transaction(transaction)

        current_time += timedelta(seconds=60)

        current_bank_balances = [current_time] + fetch_all_bank_balances(banks)
        bank_balances.append(current_bank_balances)

    write_to_csv(csv_settings.output_file_name, csv_settings.headers, bank_balances)

    return banks
