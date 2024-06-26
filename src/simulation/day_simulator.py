from datetime import timedelta
from queue import Queue
from src.simulation.offsetting import Matching
from src.simulation import settings
from src.utils.csvutils import write_to_csv
import copy


def fetch_all_bank_balances(banks):
    current_bank_balances = []
    for bank_id in banks:
        current_bank_balances.append(banks[bank_id].balance)

    return current_bank_balances


def simulate_day_transactions(banks, metrics):
    bank_balances = []
    priority_transaction_queue = Queue()
    non_priority_transaction_queue = Queue()
    current_time = settings.start_time
    matching_window = 0
    bilateral = True

    while current_time != settings.end_time:
        # Get all transactions for all banks at this timestep and put them in relevant central queue
        for bank in banks:
            banks[bank].check_for_transactions(current_time, metrics)
            bank_transactions = banks[bank].post_transactions(current_time)
            for transaction in bank_transactions:
                if transaction.priority == 1:
                    priority_transaction_queue.put(transaction)
                else:
                    non_priority_transaction_queue.put(transaction)

        # Settle all priority transactions that can be settled and keep the rest
        temp_transaction_queue = Queue()
        while not priority_transaction_queue.empty():
            transaction = priority_transaction_queue.get()
            if banks[transaction.sending_bank_id].balance - transaction.amount >= 0:
                banks[transaction.sending_bank_id].outbound_transaction(transaction)
                banks[transaction.receiving_bank_id].inbound_transaction(transaction)
                metrics.total_transaction_volume += transaction.amount
                metrics.liquidity_used += transaction.amount
            else:
                temp_transaction_queue.put(transaction)
        priority_transaction_queue = temp_transaction_queue

        if settings.day_config.LSM_enabled:
            # Run offsetting cycle and find matching payments
            if matching_window == settings.day_config.matching_window:
                if bilateral:
                    matching = Matching(banks, non_priority_transaction_queue, current_time)
                    non_priority_transaction_queue = matching.bilateral(metrics)
                    bilateral = not bilateral
                else:
                    matching = Matching(banks, non_priority_transaction_queue, current_time)
                    non_priority_transaction_queue = matching.multilateral(metrics)
                    bilateral = not bilateral
                matching_window = -20 # Cycle takes 20 seconds complete

            else:
                # Add delay to transactions
                for transaction in list(priority_transaction_queue.queue):
                    banks[transaction.sending_bank_id].add_delay()

                for transaction in list(non_priority_transaction_queue.queue):
                    banks[transaction.sending_bank_id].add_delay()

                metrics.add_bank_delay(non_priority_transaction_queue.qsize() + priority_transaction_queue.qsize())

            matching_window += 1

        else:
            temp_transaction_queue = Queue()
            while not non_priority_transaction_queue.empty():
                transaction = non_priority_transaction_queue.get()
                if banks[transaction.sending_bank_id].non_priority_balance - transaction.amount >= 0:
                    banks[transaction.sending_bank_id].outbound_transaction(transaction)
                    banks[transaction.receiving_bank_id].inbound_transaction(transaction)
                else:
                    temp_transaction_queue.put(transaction)
            non_priority_transaction_queue = temp_transaction_queue
            metrics.add_bank_delay(non_priority_transaction_queue.qsize() + priority_transaction_queue.qsize())

        current_time += timedelta(seconds=1)
        current_bank_balances = [current_time] + fetch_all_bank_balances(banks)
        bank_balances.append(current_bank_balances)

        for bank in banks:
            banks[bank].check_min_balance()

    ### Deal with deadline possible transactions - all transactions now priority (no offsetting)
    while not non_priority_transaction_queue.empty():
        priority_transaction_queue.put(non_priority_transaction_queue.get())

    for bank in banks:
        banks[bank].check_for_transactions(current_time, metrics)
        bank_transactions = banks[bank].post_transactions(current_time)
        for transaction in bank_transactions:
            priority_transaction_queue.put(transaction)

    while not priority_transaction_queue.empty():
        transaction = priority_transaction_queue.get()
        if banks[transaction.sending_bank_id].balance - transaction.amount >= 0:
            banks[transaction.sending_bank_id].outbound_transaction(transaction)
            banks[transaction.receiving_bank_id].inbound_transaction(transaction)

    current_bank_balances = [current_time + timedelta(seconds=1200)] + fetch_all_bank_balances(banks)
    bank_balances.append(current_bank_balances)

    metrics.calculate_liquidity_saved_ratio()
    print(f"Liquidity saved: {metrics.liquidity_saved_ratio*100:.2f}%")
    print(f"Average delay per transactions: {metrics.calculate_average_delay_per_transaction():.2f} minutes")
    write_to_csv(settings.csv_settings.output_file_name, settings.csv_settings.headers, bank_balances)

    return banks, metrics
