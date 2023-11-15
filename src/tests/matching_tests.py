from datetime import datetime
from queue import Queue

from src.classes.bank import NormalBank
from src.classes.transaction import DatedTransaction
from src.matching import Matching
from src.simulator import fetch_all_bank_balances


def two_banks_naive_bilateral_matching_one_way():
    banks = {0: NormalBank(0, 'A', 500, "random/random_data.csv"),
             1: NormalBank(1, 'B', 500, "random/random_data.csv")}

    time = datetime(2023, 1, 1, 5, 45)

    transaction_queue = Queue()
    transaction_queue.put(DatedTransaction(0, 1, 20, time))
    transaction_queue.put(DatedTransaction(0, 1, 40, time))
    transaction_queue.put(DatedTransaction(0, 1, 40, time))

    matching = Matching(banks, transaction_queue, time)
    matching.naive_bilateral_matching()

    balances = fetch_all_bank_balances(banks)
    assert(balances[0] == 400)
    assert(balances[1] == 600)


def two_banks_naive_bilateral_matching_two_way():
    banks = {0: NormalBank(0, 'A', 500, "random/random_data.csv"),
             1: NormalBank(1, 'B', 500, "random/random_data.csv")}

    time = datetime(2023, 1, 1, 5, 45)

    transaction_queue = Queue()
    transaction_queue.put(DatedTransaction(0, 1, 20, time))
    transaction_queue.put(DatedTransaction(1, 0, 60, time))
    transaction_queue.put(DatedTransaction(0, 1, 40, time))

    matching = Matching(banks, transaction_queue, time)
    matching.naive_bilateral_matching()

    balances = fetch_all_bank_balances(banks)
    assert(balances[0] == 500)
    assert(balances[1] == 500)


def three_banks_naive_bilateral_matching_one_way():
    banks = {0: NormalBank(0, 'A', 500, "random/random_data.csv"),
             1: NormalBank(1, 'B', 500, "random/random_data.csv"),
             2: NormalBank(2, 'C', 500, "random/random_data.csv")}

    time = datetime(2023, 1, 1, 5, 45)

    transaction_queue = Queue()
    transaction_queue.put(DatedTransaction(0, 2, 20, time))
    transaction_queue.put(DatedTransaction(0, 2, 40, time))
    transaction_queue.put(DatedTransaction(1, 2, 20, time))
    transaction_queue.put(DatedTransaction(1, 2, 40, time))

    matching = Matching(banks, transaction_queue, time)
    matching.naive_bilateral_matching()

    balances = fetch_all_bank_balances(banks)
    assert(balances[0] == 440)
    assert(balances[1] == 440)
    assert(balances[2] == 620)


def three_banks_naive_bilateral_matching_multiple_way():
    banks = {0: NormalBank(0, 'A', 500, "random/random_data.csv"),
             1: NormalBank(1, 'B', 500, "random/random_data.csv"),
             2: NormalBank(2, 'C', 500, "random/random_data.csv")}

    time = datetime(2023, 1, 1, 5, 45)

    transaction_queue = Queue()
    transaction_queue.put(DatedTransaction(0, 1, 20, time))
    transaction_queue.put(DatedTransaction(0, 2, 40, time))
    transaction_queue.put(DatedTransaction(1, 2, 20, time))
    transaction_queue.put(DatedTransaction(1, 0, 40, time))
    transaction_queue.put(DatedTransaction(2, 0, 20, time))
    transaction_queue.put(DatedTransaction(2, 1, 40, time))

    matching = Matching(banks, transaction_queue, time)
    matching.naive_bilateral_matching()

    balances = fetch_all_bank_balances(banks)
    for balance in balances:
        print(balance)
    assert(balances[0] == 500)
    assert(balances[1] == 500)
    assert(balances[2] == 500)


def main():
    """
    two_banks_naive_bilateral_matching_one_way()
    two_banks_naive_bilateral_matching_two_way()
    three_banks_naive_bilateral_matching_one_way()
    """
    three_banks_naive_bilateral_matching_multiple_way()


main()
