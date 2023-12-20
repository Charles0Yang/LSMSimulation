from datetime import timedelta
from queue import Queue
import json

from src.classes.bank import Bank
from src.classes.transaction import DatedTransaction
import networkx as nx
import matplotlib.pyplot as plt


def display_graph(g):
    pos = nx.spring_layout(g)  # You can use different layout algorithms
    nx.draw(g, pos, with_labels=True, node_size=700, node_color="skyblue", font_size=10, font_color="black",
            connectionstyle="arc3, rad=0.1")

    edge_labels = {(u, v): f"{d['weight']}" for u, v, d in g.edges(data=True)}
    nx.draw_networkx_edge_labels(g, pos, edge_labels=edge_labels, font_color='red', label_pos=0.4)

    plt.show()


class Matching:

    def __init__(self, banks, transaction_queue, time):
        self.banks = banks
        self.transaction_queue = transaction_queue
        self.time = time

    def naive_bilateral_matching(self):
        send_receive_pairs = {}
        transactions = list(self.transaction_queue.queue)
        while not self.transaction_queue.empty():
            transaction = self.transaction_queue.get()

            send_receive_pair = (transaction.sending_bank_id, transaction.receiving_bank_id)
            reverse_pair = (transaction.receiving_bank_id, transaction.sending_bank_id)

            if send_receive_pair in send_receive_pairs.keys():
                send_receive_pairs[send_receive_pair] += transaction.amount

            elif reverse_pair in send_receive_pairs.keys():
                send_receive_pairs[reverse_pair] -= transaction.amount

            else:
                send_receive_pairs[send_receive_pair] = transaction.amount

        for pair in send_receive_pairs:
            amount = send_receive_pairs[pair]
            sending_bank_id, receiving_bank_id = pair
            if amount < 0:
                sending_bank_id, receiving_bank_id = receiving_bank_id, sending_bank_id
                amount = -amount

            while self.banks[sending_bank_id].balance - amount < 0:
                transaction_to_remove = self.remove_bank_last_transaction(transactions, sending_bank_id)
                amount -= transaction_to_remove.amount

            transaction = DatedTransaction(sending_bank_id, receiving_bank_id, amount, self.time)
            self.banks[sending_bank_id].outbound_transaction(transaction)
            self.banks[receiving_bank_id].inbound_transaction(transaction)

        return Queue()

    def graph_bilateral_offsetting(self):

        g = self.build_graph()
        transactions_to_do = Queue()

        for edge in g.edges():
            bank_one, bank_two = edge
            if g.has_edge(bank_two, bank_one):
                amount_one = g.get_edge_data(bank_one, bank_two)["weight"]
                amount_two = g.get_edge_data(bank_two, bank_one)["weight"]
                offset_amount = abs(amount_two - amount_one)
                if amount_one > amount_two:
                    transactions_to_do.put(DatedTransaction(bank_one, bank_two, offset_amount, self.time))
                elif amount_one < amount_two:
                    transactions_to_do.put(DatedTransaction(bank_two, bank_one, offset_amount, self.time))
                g.remove_edge(bank_two, bank_one)
            else:
                transactions_to_do.put(
                    DatedTransaction(bank_one, bank_two, g.get_edge_data(bank_one, bank_two)["weight"], self.time))

        while not transactions_to_do.empty():
            transaction = transactions_to_do.get()
            sending_bank = self.banks[transaction.sending_bank_id]
            receiving_bank = self.banks[transaction.receiving_bank_id]

            sending_bank.outbound_transaction(transaction)
            receiving_bank.inbound_transaction(transaction)

    def bilateral_offsetting(self):
        send_receive_pairs = {}
        transactions = list(self.transaction_queue.queue)
        carryover_transactions = Queue()
        while not self.transaction_queue.empty():
            transaction = self.transaction_queue.get()

            send_receive_pair = (transaction.sending_bank_id, transaction.receiving_bank_id)
            reverse_pair = (transaction.receiving_bank_id, transaction.sending_bank_id)

            if send_receive_pair in send_receive_pairs.keys():
                send_receive_pairs[send_receive_pair] += transaction.amount

            elif reverse_pair in send_receive_pairs.keys():
                send_receive_pairs[reverse_pair] -= transaction.amount

            else:
                send_receive_pairs[send_receive_pair] = transaction.amount

        for pair in send_receive_pairs:
            amount = send_receive_pairs[pair]
            sending_bank_id, receiving_bank_id = pair
            if amount < 0:
                sending_bank_id, receiving_bank_id = receiving_bank_id, sending_bank_id
                amount = -amount

            while self.banks[sending_bank_id].balance - amount < 0:
                transaction_to_remove = self.remove_bank_last_transaction(transactions, sending_bank_id)
                amount -= transaction_to_remove.amount
                carryover_transactions.put(transaction_to_remove)

            transaction = DatedTransaction(sending_bank_id, receiving_bank_id, amount, self.time)
            self.banks[sending_bank_id].outbound_transaction(transaction)
            self.banks[receiving_bank_id].inbound_transaction(transaction)

        return carryover_transactions

    def multilateral_offsetting(self):
        balances = {self.banks[bank].id: self.banks[bank].non_priority_balance for bank in self.banks}
        transactions_to_do = list(self.transaction_queue.queue)
        transactions_to_carryover = []
        for transaction in transactions_to_do:
            balances[transaction.sending_bank_id] -= transaction.amount
            balances[transaction.receiving_bank_id] += transaction.amount

        while not self.bank_balances_positive(balances):
            for bank in balances:
                if int(balances[bank]) < 0:
                    transaction = self.remove_bank_last_transaction(transactions_to_do, bank)
                    balances[transaction.sending_bank_id] += transaction.amount
                    balances[transaction.receiving_bank_id] -= transaction.amount
                    transactions_to_do.remove(transaction)
                    transactions_to_carryover.insert(0, transaction)
                    break

        for transaction in transactions_to_do:
            transaction.time += timedelta(seconds=20) # Transactions all go through at end of cycle
            sending_bank = self.banks[transaction.sending_bank_id]
            receiving_bank = self.banks[transaction.receiving_bank_id]

            sending_bank.outbound_transaction(transaction)
            receiving_bank.inbound_transaction(transaction)

        self.transaction_queue = Queue()
        for transaction in transactions_to_carryover:
            self.transaction_queue.put(transaction)

        return self.transaction_queue

    def remove_bank_last_transaction(self, transactions, bank_id):
        for transaction in reversed(transactions):
            if transaction.sending_bank_id == bank_id:
                return transaction

    def bank_balances_positive(self, balances):
        return all(int(balance) >= 0 for balance in balances.values())

    def build_graph(self):

        g = nx.DiGraph()
        for bank in self.banks:
            g.add_node(bank)

        while not self.transaction_queue.empty():
            transaction = self.transaction_queue.get()
            sending_bank = transaction.sending_bank_id
            receiving_bank = transaction.receiving_bank_id
            if g.has_edge(sending_bank, receiving_bank):
                g[sending_bank][receiving_bank]["weight"] += transaction.amount
            else:
                g.add_edge(sending_bank,
                           receiving_bank,
                           weight=transaction.amount)

        return g
