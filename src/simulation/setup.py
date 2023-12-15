from datetime import datetime, timedelta
from queue import Queue

from src.classes.bank import Bank, NormalBank, DelayBank
from src.classes.configs.csv_config import CSVSettings
from src.classes.configs.day_config import DayConfig
from src.classes.transaction import DatedTransaction
from src.matching import Matching
from src.utils.csvutils import read_csv, write_to_csv


def generate_banks(bank_types, starting_balance, input_file):
    banks = {}
    bank_name = "A"
    bank_num = 0
    for i in range(len(bank_types)):
        if i == 0:
            for j in range(bank_types[i]):
                banks[bank_num] = NormalBank(bank_num, bank_name, starting_balance, input_file)
                bank_num += 1
        if i == 1:
            for k in range(bank_types[i]):
                banks[bank_num] = DelayBank(bank_num, bank_name, starting_balance, input_file, 120)
                bank_num += 1

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
