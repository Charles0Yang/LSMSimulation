from datetime import datetime
from src.classes.bank import NormalBank, DelayBank
from src.classes.transaction import DatedTransaction
from src.simulation import settings
from src.utils.csvutils import read_csv


def generate_banks(bank_types, starting_balance, input_file):
    banks = {}
    bank_name = "A"
    bank_num = 0
    print(bank_types)
    # First n banks are normal banks, rest are delay banks
    for i in range(len(bank_types)):
        if i == 0:
            for j in range(bank_types[i]):
                banks[bank_num] = NormalBank(bank_num, bank_name, starting_balance, input_file)
                bank_num += 1
                bank_name = chr(ord(bank_name) + 1)
        if i == 1:
            for k in range(bank_types[i]):
                banks[bank_num] = DelayBank(bank_num, bank_name, starting_balance, input_file, settings.delay_amount)
                bank_num += 1
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
