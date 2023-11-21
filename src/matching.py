from queue import Queue

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

            transaction = DatedTransaction(sending_bank_id, receiving_bank_id, amount, self.time)
            self.banks[sending_bank_id].outbound_transaction(transaction)
            self.banks[receiving_bank_id].inbound_transaction(transaction)

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
                transactions_to_do.put(DatedTransaction(bank_one, bank_two, g.get_edge_data(bank_one, bank_two)["weight"], self.time))

        while not transactions_to_do.empty():
            transaction = transactions_to_do.get()
            sending_bank = self.banks[transaction.sending_bank_id]
            receiving_bank = self.banks[transaction.receiving_bank_id]

            sending_bank.outbound_transaction(transaction)
            receiving_bank.inbound_transaction(transaction)

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

