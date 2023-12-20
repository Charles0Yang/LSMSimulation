from datetime import datetime
from src.classes.bank import NormalBank, DelayBank
from src.classes.transaction import DatedTransaction
from src.simulation import settings
from src.utils.csvutils import read_csv


def generate_banks(bank_types, starting_balance, input_file):
    banks = {}
    bank_name = "A"
    bank_num = 0
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

