from datetime import datetime, timedelta
from queue import Queue

from src.classes.configs.csv_config import CSVSettings
from src.classes.configs.day_config import DayConfig
from src.matching import Matching
from src.utils.csvutils import write_to_csv


def fetch_all_bank_balances(banks):
    current_bank_balances = []
    for bank_id in banks:
        current_bank_balances.append(banks[bank_id].balance)

    return current_bank_balances


def simulate_day_transactions(day_config: DayConfig, csv_settings: CSVSettings, banks):
    start_time = datetime(2023, 1, 1, 5, 45)
    end_time = datetime(2023, 1, 1, 18, 20)

    bank_balances = []

    transaction_queue = Queue()

    current_time = start_time
    matching_window = 0
    while current_time != end_time:

        for bank in banks:
            banks[bank].check_for_transactions(current_time)
            bank_transactions = banks[bank].post_transactions(current_time)
            for transaction in bank_transactions:
                transaction_queue.put(transaction)

        if not day_config.LSM_enabled:
            temp_transaction_queue = Queue()
            while not transaction_queue.empty():
                transaction = transaction_queue.get()
                if banks[transaction.sending_bank_id].balance - transaction.amount >= 0:
                    banks[transaction.sending_bank_id].outbound_transaction(transaction)
                    banks[transaction.receiving_bank_id].inbound_transaction(transaction)
                else:
                    temp_transaction_queue.put(transaction)
            transaction_queue = temp_transaction_queue

        else:
            if matching_window == day_config.matching_window:
                matching = Matching(banks, transaction_queue, current_time)
                transaction_queue = matching.bilateral_offsetting()
                matching_window = 0

            matching_window += 1

        current_time += timedelta(seconds=1)

        current_bank_balances = [current_time] + fetch_all_bank_balances(banks)
        bank_balances.append(current_bank_balances)

    ### Deal with deadline possible transactions

    for bank in banks:
        banks[bank].check_for_transactions(current_time)
        bank_transactions = banks[bank].post_transactions(current_time)
        for transaction in bank_transactions:
            transaction_queue.put(transaction)

    while not transaction_queue.empty():
        transaction = transaction_queue.get()
        banks[transaction.sending_bank_id].outbound_transaction(transaction)
        banks[transaction.receiving_bank_id].inbound_transaction(transaction)

    current_bank_balances = [current_time + timedelta(seconds=1200)] + fetch_all_bank_balances(banks)
    bank_balances.append(current_bank_balances)

    write_to_csv(csv_settings.output_file_name, csv_settings.headers, bank_balances)

    return banks
