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
    assert (balances[0] == 400)
    assert (balances[1] == 600)


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
    assert (balances[0] == 500)
    assert (balances[1] == 500)


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
    assert (balances[0] == 440)
    assert (balances[1] == 440)
    assert (balances[2] == 620)


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
    transaction_queue.put(DatedTransaction(0, 1, 20, time))
    transaction_queue.put(DatedTransaction(0, 2, 20, time))

    matching = Matching(banks, transaction_queue, time)
    matching.naive_bilateral_matching()

    balances = fetch_all_bank_balances(banks)

    assert (balances[0] == 460)
    assert (balances[1] == 520)
    assert (balances[2] == 520)


def three_banks_graph_bilateral_matching_one_way():
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
    matching.graph_bilateral_offsetting()

    balances = fetch_all_bank_balances(banks)

    assert (balances[0] == 440)
    assert (balances[1] == 440)
    assert (balances[2] == 620)


def three_banks_graph_bilateral_matching_multiple_way():
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
    transaction_queue.put(DatedTransaction(0, 1, 20, time))
    transaction_queue.put(DatedTransaction(0, 2, 20, time))

    matching = Matching(banks, transaction_queue, time)
    matching.graph_bilateral_offsetting()

    balances = fetch_all_bank_balances(banks)

    assert (balances[0] == 460)
    assert (balances[1] == 520)
    assert (balances[2] == 520)


def three_banks_multilateral_matching_reject_all_transactions():
    banks = {0: NormalBank(0, 'A', 0, "random/random_data.csv"),
             1: NormalBank(1, 'B', 20, "random/random_data.csv"),
             2: NormalBank(2, 'C', 30, "random/random_data.csv")}

    time = datetime(2023, 1, 1, 5, 45)

    transaction_queue = Queue()
    transaction_queue.put(DatedTransaction(0, 1, 20, time))
    transaction_queue.put(DatedTransaction(1, 0, 50, time))
    transaction_queue.put(DatedTransaction(2, 1, 40, time))

    matching = Matching(banks, transaction_queue, time)
    carryover_transactions = matching.multilateral_offsetting()

    balances = fetch_all_bank_balances(banks)

    expected_transactions = Queue()
    expected_transactions.put(DatedTransaction(0, 1, 20, time))
    expected_transactions.put(DatedTransaction(1, 0, 50, time))
    expected_transactions.put(DatedTransaction(2, 1, 40, time))

    assert (balances[0] == 0)
    assert (balances[1] == 20)
    assert (balances[2] == 30)
    assert (are_queues_equal(carryover_transactions, expected_transactions))


def three_banks_multilateral_matching_simple_accept_all_transactions():
    banks = {0: NormalBank(0, 'A', 20, "random/random_data.csv"),
             1: NormalBank(1, 'B', 20, "random/random_data.csv"),
             2: NormalBank(2, 'C', 30, "random/random_data.csv")}

    time = datetime(2023, 1, 1, 5, 45)

    transaction_queue = Queue()
    transaction_queue.put(DatedTransaction(0, 1, 20, time))
    transaction_queue.put(DatedTransaction(1, 0, 20, time))
    transaction_queue.put(DatedTransaction(2, 1, 30, time))

    matching = Matching(banks, transaction_queue, time)
    carryover_transactions = matching.multilateral_offsetting()

    balances = fetch_all_bank_balances(banks)

    assert (balances[0] == 20)
    assert (balances[1] == 50)
    assert (balances[2] == 0)
    assert (carryover_transactions.qsize() == 0)


def three_banks_multilateral_matching_complex_accept_all_transactions():
    banks = {0: NormalBank(0, 'A', 20, "random/random_data.csv"),
             1: NormalBank(1, 'B', 20, "random/random_data.csv"),
             2: NormalBank(2, 'C', 30, "random/random_data.csv")}

    time = datetime(2023, 1, 1, 5, 45)

    transaction_queue = Queue()
    transaction_queue.put(DatedTransaction(0, 1, 30, time))
    transaction_queue.put(DatedTransaction(1, 0, 40, time))
    transaction_queue.put(DatedTransaction(2, 1, 30, time))

    matching = Matching(banks, transaction_queue, time)
    carryover_transactions = matching.multilateral_offsetting()

    balances = fetch_all_bank_balances(banks)

    assert (balances[0] == 30)
    assert (balances[1] == 40)
    assert (balances[2] == 0)
    assert (carryover_transactions.qsize() == 0)


def three_banks_multilateral_matching_accept_and_reject_transactions():
    banks = {0: NormalBank(0, 'A', 20, "random/random_data.csv"),
             1: NormalBank(1, 'B', 20, "random/random_data.csv"),
             2: NormalBank(2, 'C', 30, "random/random_data.csv")}

    time = datetime(2023, 1, 1, 5, 45)

    transaction_queue = Queue()
    transaction_queue.put(DatedTransaction(0, 1, 30, time))
    transaction_queue.put(DatedTransaction(1, 0, 30, time))
    transaction_queue.put(DatedTransaction(2, 1, 50, time))

    matching = Matching(banks, transaction_queue, time)
    carryover_transactions = matching.multilateral_offsetting()

    balances = fetch_all_bank_balances(banks)

    expected_transactions = Queue()
    expected_transactions.put(DatedTransaction(2, 1, 50, time))

    assert (balances[0] == 20)
    assert (balances[1] == 20)
    assert (balances[2] == 30)
    assert (are_queues_equal(carryover_transactions, expected_transactions))


def three_banks_bilateral_matching_complex_accept_all_transactions():
    banks = {0: NormalBank(0, 'A', 20, "random/random_data.csv"),
             1: NormalBank(1, 'B', 20, "random/random_data.csv"),
             2: NormalBank(2, 'C', 30, "random/random_data.csv")}

    time = datetime(2023, 1, 1, 5, 45)

    transaction_queue = Queue()
    transaction_queue.put(DatedTransaction(0, 1, 30, time))
    transaction_queue.put(DatedTransaction(1, 0, 40, time))
    transaction_queue.put(DatedTransaction(2, 1, 30, time))

    matching = Matching(banks, transaction_queue, time)
    carryover_transactions = matching.bilateral_offsetting()

    balances = fetch_all_bank_balances(banks)

    assert (balances[0] == 30)
    assert (balances[1] == 40)
    assert (balances[2] == 0)
    assert (carryover_transactions.qsize() == 0)


def three_banks_multilateral_matching_reject_all_transactions():
    banks = {0: NormalBank(0, 'A', 0, "random/random_data.csv"),
             1: NormalBank(1, 'B', 20, "random/random_data.csv"),
             2: NormalBank(2, 'C', 30, "random/random_data.csv")}

    time = datetime(2023, 1, 1, 5, 45)

    transaction_queue = Queue()
    transaction_queue.put(DatedTransaction(0, 1, 20, time))
    transaction_queue.put(DatedTransaction(1, 0, 50, time))
    transaction_queue.put(DatedTransaction(2, 1, 40, time))

    matching = Matching(banks, transaction_queue, time)
    carryover_transactions = matching.bilateral_offsetting()

    balances = fetch_all_bank_balances(banks)

    expected_transactions = Queue()
    expected_transactions.put(DatedTransaction(0, 1, 20, time))
    expected_transactions.put(DatedTransaction(1, 0, 50, time))
    expected_transactions.put(DatedTransaction(2, 1, 40, time))

    for balance in balances:
        print(balance)

    assert (balances[0] == 0)
    assert (balances[1] == 20)
    assert (balances[2] == 30)
    assert (are_queues_equal(carryover_transactions, expected_transactions))


def are_queues_equal(a, b):
    if a.qsize() != b.qsize():
        return False

    while not a.empty():
        a_item = a.get()
        b_item = b.get()

        if a_item.amount != b_item.amount or a_item.sending_bank_id != b_item.sending_bank_id or a_item.receiving_bank_id != b_item.receiving_bank_id or a_item.time != b_item.time:
            return False

    return True


def main():
    two_banks_naive_bilateral_matching_one_way()
    two_banks_naive_bilateral_matching_two_way()
    three_banks_naive_bilateral_matching_one_way()
    three_banks_naive_bilateral_matching_multiple_way()
    three_banks_graph_bilateral_matching_one_way()
    three_banks_graph_bilateral_matching_multiple_way()
    three_banks_bilateral_matching_complex_accept_all_transactions()
    three_banks_multilateral_matching_reject_all_transactions()
    three_banks_multilateral_matching_simple_accept_all_transactions()
    three_banks_multilateral_matching_complex_accept_all_transactions()
    three_banks_multilateral_matching_accept_and_reject_transactions()


main()
