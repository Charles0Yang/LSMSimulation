from src.classes.bank import Bank
from src.classes.transaction import DatedTransaction
import networkx as nx


class Matching:

    def __init__(self, banks, transaction_queue, timestep):
        self.banks = banks
        self.transaction_queue = transaction_queue
        self.timestep = timestep

    def naive_bilateral_matching(self):

        send_receive_pairs = {}
        while not self.transaction_queue.empty():
            transaction = self.transaction_queue.get()
            send_receive_pair = (self.banks[transaction.sending_bank_id], self.banks[transaction.receiving_bank_id])
            reverse_pair = (self.banks[transaction.receiving_bank_id], self.banks[transaction.sending_bank_id])

            if send_receive_pair in send_receive_pairs:
                send_receive_pairs[send_receive_pair] += transaction.amount

            elif reverse_pair in send_receive_pairs:
                send_receive_pairs[reverse_pair] -= transaction.amount

            else:
                send_receive_pairs[send_receive_pair] = transaction.amount

        for pair in send_receive_pairs:
            amount = send_receive_pairs[pair]
            sending_bank, receiving_bank = pair

            transaction = DatedTransaction(self.timestep, sending_bank.id, receiving_bank.id, amount)

            sending_bank.outbound_transaction(transaction)
            receiving_bank.inbound_transaction(transaction)

    def naive_multilateral_offsetting(self):

        G = self.build_graph()
        changes = False

        while not changes:
            for node in G.nodes():
                edges = list(G.out_edges(node))



        new_transactions = []

        for transaction in new_transactions:
            sending_bank = self.banks[transaction.sending_bank_id]
            receiving_bank = self.banks[transaction.receiving_bank_id]

            sending_bank.outbound_transaction(transaction)
            receiving_bank.inbound_transaction(transaction)

    def build_graph(self):

        G = nx.DiGraph()

        for bank in self.banks:
            G.add_node(bank)

        while not self.transaction_queue.empty():
            transaction = self.transaction_queue.get()
            sending_bank = self.banks[transaction.sending_bank_id]
            receiving_bank = self.banks[transaction.receiving_bank_id]
            if G.has_edge(sending_bank, receiving_bank):
                G[sending_bank][receiving_bank]["weight"] += transaction.amount
            else:
                G.add_edge(sending_bank,
                           receiving_bank,
                           weight=transaction.amount)

        return G
