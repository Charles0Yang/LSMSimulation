from datetime import timedelta, datetime
from queue import Queue
import time
import numpy as np
import matplotlib.pyplot as plt

from src.classes.DP import Bank
from src.classes.configs.csv_config import CSVSettings
from src.classes.configs.data_generation_config import DataGenerationConfig
from src.classes.payment import DatedTransaction
from src.data_scripts.basic_generation import generate_data
from src.simulation.setup import generate_banks
import networkx as nx
import matplotlib.pyplot as plt

from src.simulation.metrics import Metrics


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
        self.logging = False

    def naive_bilateral_matching(self):
        send_receive_pairs = {}
        transactions = list(self.transaction_queue.queue)
        transactions_to_redo = Queue()
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
                transactions_to_redo.put(transaction_to_remove)
                amount -= transaction_to_remove.amount

            transaction = DatedTransaction(sending_bank_id, receiving_bank_id, amount, self.time, 0)
            self.banks[sending_bank_id].outbound_transaction(transaction)
            self.banks[receiving_bank_id].inbound_transaction(transaction)

        return transactions_to_redo

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

        return transactions_to_do

    def bilateral_offsetting(self, metrics):
        balances = {self.banks[bank].id: self.banks[bank].non_priority_balance for bank in self.banks}
        raw_balances_before = [balances[bank] for bank in balances]
        transactions_to_do = []
        num_transactions = self.transaction_queue.qsize()
        all_transactions = list(self.transaction_queue.queue)
        transactions_to_carryover = []
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

            while balances[sending_bank_id] - amount < 0:
                if self.find_bank_last_transaction_specific(all_transactions, sending_bank_id, receiving_bank_id) == -1:
                    break
                transaction_to_remove = self.find_bank_last_transaction_specific(all_transactions, sending_bank_id, receiving_bank_id)
                amount -= transaction_to_remove.amount
                transactions_to_carryover.insert(0, transaction_to_remove)
                all_transactions.remove(transaction_to_remove)

                if amount < 0:
                    sending_bank_id, receiving_bank_id = receiving_bank_id, sending_bank_id
                    amount = -amount

            balances[sending_bank_id] -= amount
            balances[receiving_bank_id] += amount
            assert(balances[sending_bank_id] >= 0)
            transactions_to_do.append(DatedTransaction(sending_bank_id, receiving_bank_id, amount, self.time, 0))

        for transaction in transactions_to_do:
            self.banks[transaction.sending_bank_id].outbound_transaction(transaction)
            self.banks[transaction.receiving_bank_id].inbound_transaction(transaction)

        balances = {self.banks[bank].id: self.banks[bank].non_priority_balance for bank in self.banks}
        raw_balances_after = [balances[bank] for bank in balances]
        metrics.add_to_liquidity_and_transaction_volumes(raw_balances_before, raw_balances_after, all_transactions)
        if num_transactions > 0:
            metrics.offset_ratio.append(100 * (1 - len(transactions_to_carryover) / num_transactions))
        else:
            metrics.offset_ratio.append(0)

        self.transaction_queue = Queue()
        for transaction in transactions_to_carryover:
            self.transaction_queue.put(transaction)
        metrics.transactions_carried_over += len(transactions_to_carryover)
        return self.transaction_queue

    def multilateral_offsetting(self, metrics):
        balances = {self.banks[bank].id: self.banks[bank].non_priority_balance for bank in self.banks}
        assert(self.bank_balances_positive(balances))
        raw_balances_before = [balances[bank] for bank in balances]
        transactions_to_do = list(self.transaction_queue.queue)
        num_transactions = len(transactions_to_do)
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

        raw_balances_after = [balances[bank] for bank in balances]
        metrics.add_to_liquidity_and_transaction_volumes(raw_balances_before, raw_balances_after, transactions_to_do)
        if num_transactions > 0 :
            metrics.offset_ratio.append(100 * (1 - len(transactions_to_carryover)/num_transactions))
        else:
            metrics.offset_ratio.append(0)
        metrics.transactions_carried_over += len(transactions_to_carryover)
        return self.transaction_queue

    def remove_bank_last_transaction(self, transactions, bank_id):
        for transaction in reversed(transactions):
            if transaction.sending_bank_id == bank_id:
                return transaction
        return -1

    def find_bank_last_transaction_specific(self, transactions, sending_bank_id, receiving_bank_id):
        for transaction in reversed(transactions):
            if transaction.sending_bank_id == sending_bank_id and transaction.receiving_bank_id == receiving_bank_id:
                return transaction
        return -1

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

    def bilateral(self, metrics):
        # Get non-priority balances of all banks first
        # All balances positive
        balances = {self.banks[bank].id: self.banks[bank].non_priority_balance for bank in self.banks}
        raw_balances_before = [balances[bank] for bank in balances]
        assert ([x >= 0 for x in raw_balances_before])

        # Create copy of initial transaction list
        all_transactions = list(self.transaction_queue.queue) # To mutate
        all_transactions_immutable = list(self.transaction_queue.queue)
        num_transactions = len(all_transactions)
        transactions_to_carryover = []

        # Find bilateral balances
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

        # Ensure all pairs are positive
        for pair in send_receive_pairs:
            amount = send_receive_pairs[pair]
            sending, receiving = pair
            if amount < 0:
                sending, receiving = receiving, sending
                amount = -amount

            while balances[sending] - amount < 0:
                if self.find_bank_last_transaction_specific(all_transactions, sending, receiving) == -1:
                    break
                transaction_to_remove = self.find_bank_last_transaction_specific(all_transactions, sending,
                                                                                 receiving)
                amount -= transaction_to_remove.amount
                # Add transaction to carryover list
                transactions_to_carryover.insert(0, transaction_to_remove)
                # Remove transaction from solution list
                all_transactions.remove(transaction_to_remove)

                # In the case that removing a transaction switches the net position, switch the sender and receiver
                if amount < 0:
                    sending, receiving = receiving, sending
                    amount = -amount

            # Update balances for each pair
            balances[sending] -= amount
            balances[receiving] += amount
            assert (int(balances[sending]) >= 0)
            assert (int(balances[receiving]) >= 0)

        # Carry out transactions in solution list
        for transaction in all_transactions:
            self.banks[transaction.sending_bank_id].outbound_transaction(transaction)
            self.banks[transaction.receiving_bank_id].inbound_transaction(transaction)

        # Get post non-priority balances of all banks
        balances = {self.banks[bank].id: self.banks[bank].non_priority_balance for bank in self.banks}
        raw_balances_after = [balances[bank] for bank in balances]

        # Calculate the liquidity savings using prior and post balances, and transactions in solution list
        metrics.add_to_liquidity_and_transaction_volumes(raw_balances_before, raw_balances_after, all_transactions)

        # Calculate offset ratio
        if num_transactions > 0:
            metrics.offset_ratio.append(100 * (len(all_transactions) / num_transactions))
        else:
            metrics.offset_ratio.append(0)

        # Carry over relevant transactions as queue
        self.transaction_queue = Queue()
        for transaction in transactions_to_carryover:
            self.transaction_queue.put(transaction)
        metrics.transactions_carried_over += len(transactions_to_carryover)

        # Logging
        if self.logging:
            print(f"{self.time}: Prior balances {raw_balances_before}")
            print(f"{self.time}: Original transactions {all_transactions_immutable}")
            print(f"{self.time}: Carryover transactions {transactions_to_carryover}")
            print(f"{self.time}: Matched transactions {all_transactions}")
            print(f"{self.time}: Post balances {raw_balances_after}")

        return self.transaction_queue

    def multilateral(self, metrics):
        # Get non-priority balances of all banks first
        # All balances positive
        balances = {self.banks[bank].id: self.banks[bank].non_priority_balance for bank in self.banks}
        raw_balances_before = [balances[bank] for bank in balances]
        assert ([x >= 0 for x in raw_balances_before])

        # Create copy of initial transaction list
        all_transactions = list(self.transaction_queue.queue)
        all_transactions_immutable = list(self.transaction_queue.queue)
        num_transactions = len(all_transactions)
        transactions_to_carryover = []

        # Find multilateral balances
        for transaction in all_transactions:
            balances[transaction.sending_bank_id] -= transaction.amount
            balances[transaction.receiving_bank_id] += transaction.amount

        # Determine which payments to include in solution list
        while not self.bank_balances_positive(balances):
            for bank in balances:
                while int(balances[bank]) < 0:
                    transaction_to_remove = self.remove_bank_last_transaction(all_transactions, bank)
                    if transaction_to_remove != -1:
                        balances[bank] += transaction_to_remove.amount
                        balances[transaction_to_remove.receiving_bank_id] -= transaction_to_remove.amount
                        # Add transaction to carryover list
                        transactions_to_carryover.insert(0, transaction_to_remove)
                        # Remove transaction from solution list
                        all_transactions.remove(transaction_to_remove)
                    else:
                        break

        # Assert all bank balances positive
        assert (self.bank_balances_positive(balances))

        # Carry out transactions in solution list
        for transaction in all_transactions:
            self.banks[transaction.sending_bank_id].outbound_transaction(transaction)
            self.banks[transaction.receiving_bank_id].inbound_transaction(transaction)

        # Get post non-priority balances of all banks
        balances = {self.banks[bank].id: self.banks[bank].non_priority_balance for bank in self.banks}
        raw_balances_after = [balances[bank] for bank in balances]

        # Calculate the liquidity savings using prior and post balances, and transactions in solution list
        metrics.add_to_liquidity_and_transaction_volumes(raw_balances_before, raw_balances_after, all_transactions)

        # Calculate offset ratio
        if num_transactions > 0:
            metrics.offset_ratio.append(100 * (len(all_transactions) / num_transactions))
        else:
            metrics.offset_ratio.append(0)

        # Carry over relevant transactions as queue
        self.transaction_queue = Queue()
        for transaction in transactions_to_carryover:
            self.transaction_queue.put(transaction)
        metrics.transactions_carried_over += len(transactions_to_carryover)

        # Logging
        if self.logging:
            print(f"{self.time}: Prior balances {raw_balances_before}")
            print(f"{self.time}: Original transactions {all_transactions_immutable}")
            print(f"{self.time}: Carryover transactions {transactions_to_carryover}")
            print(f"{self.time}: Matched transactions {all_transactions}")
            print(f"{self.time}: Post balances {raw_balances_after}")

        return self.transaction_queue

# Define a function to measure the execution time of each algorithm
def measure_execution_time():

    bilateral_execution_times = []
    multilateral_execution_times = []

    transaction_nums = []
    num = 10
    while num <= 100:
        transaction_nums.append(num)
        if num < 100:
            num += 10
        elif num < 1000:
            num += 50
        elif num < 10000:
            num += 100
        elif num <= 50000:
            num += 1000

    bilateral_metrics = Metrics()
    multilateral_metrics = Metrics()
    for num in transaction_nums:
        print(num)
        data_generation_config = DataGenerationConfig(
            num_banks=10,
            num_transactions=num,
            min_transaction_amount=1,
            max_transaction_amount=20
        )

        generate_data(data_generation_config)
        banks = generate_banks([10, 0, 0, 0], 100, 'random/random_data.csv')
        transactionQueue = Queue()
        for bank in banks:
            for transaction in banks[bank].transactions_to_do:
                transactionQueue.put(transaction)
        offsetting = Matching(banks, transactionQueue, datetime(2023, 1, 1, 5, 45))
        start_time = time.time()
        result = offsetting.bilateral_offsetting(bilateral_metrics)
        end_time = time.time()
        bilateral_time = end_time - start_time

        banks = generate_banks([10, 0, 0, 0], 100, 'random/random_data.csv')
        transactionQueue = Queue()
        for bank in banks:
            for transaction in banks[bank].transactions_to_do:
                transactionQueue.put(transaction)
        offsetting = Matching(banks, transactionQueue, datetime(2023, 1, 1, 5, 45))
        start_time = time.time()
        result = offsetting.multilateral_offsetting(multilateral_metrics)
        end_time = time.time()
        multilateral_time = end_time - start_time

        # Compare the execution times
        bilateral_execution_times.append(bilateral_time)
        multilateral_execution_times.append(multilateral_time)

    x = transaction_nums
    data1 = bilateral_metrics.offset_ratio
    data2 = multilateral_metrics.offset_ratio
    window_size = 40
    smoothed_data1 = np.convolve(data1, np.ones(window_size) / window_size, mode='valid')
    smoothed_data2 = np.convolve(data2, np.ones(window_size) / window_size, mode='valid')
    smoothed_x = x[(window_size - 1) // 2: -(window_size - 1) // 2]  # Adjust x values accordingly

    # Plot the original and smoothed data
    plt.plot(x, data1, label='Bilateral offsetting offset ratio', color='blue')
    plt.plot(x, data2, label='Multilateral offsetting offset ratio', color='red')

    # Add labels and legend
    plt.xlabel('Payment Volume')
    plt.ylabel('Offset Ratio %')
    plt.title('Impact of Payment Volume on Offset Ratio')
    plt.legend()
    plt.savefig('offsetting_ratio.png')
    # Show plot
    plt.show()

def test():
    transaction_nums = []
    num = 10
    while num <= 50000:
        transaction_nums.append(num)
        if num < 100:
            num += 10
        elif num < 1000:
            num += 50
        elif num < 10000:
            num += 100
        elif num <= 50000:
            num += 1000
    x = transaction_nums

    data1 = [0.0, 0.0, 0.0, 0.0, 0.0, 1.6666666666666667, 0.0, 1.25, 4.444444444444445, 7.0, 0.6666666666666666, 4.5, 2.4, 8.666666666666666, 35.142857142857146, 41.25, 10.666666666666666, 6.8, 12.727272727272727, 5.0, 2.3076923076923075, 7.857142857142857, 8.933333333333334, 8.75, 4.0, 4.111111111111111, 3.5789473684210527, 4.1, 4.7272727272727275, 5.166666666666667, 4.6923076923076925, 17.357142857142858, 5.133333333333334, 18.0, 3.9411764705882355, 5.0, 32.89473684210526, 13.5, 10.666666666666666, 12.772727272727273, 10.130434782608695, 19.791666666666668, 3.72, 21.846153846153847, 6.925925925925926, 17.071428571428573, 2.4827586206896552, 5.466666666666667, 5.258064516129032, 25.28125, 5.151515151515151, 3.264705882352941, 15.228571428571428, 19.555555555555557, 14.0, 5.2894736842105265, 5.666666666666667, 5.4, 5.2926829268292686, 7.761904761904762, 13.86046511627907, 16.272727272727273, 3.688888888888889, 4.543478260869565, 3.617021276595745, 23.3125, 3.489795918367347, 12.28, 5.235294117647059, 18.557692307692307, 9.452830188679245, 12.722222222222221, 32.07272727272727, 18.303571428571427, 14.789473684210526, 4.362068965517241, 5.033898305084746, 12.766666666666667, 3.3278688524590163, 9.693548387096774, 4.158730158730159, 21.921875, 16.43076923076923, 6.287878787878788, 6.044776119402985, 3.8529411764705883, 4.536231884057971, 5.014285714285714, 3.323943661971831, 14.23611111111111, 11.945205479452055, 2.891891891891892, 3.7066666666666666, 4.868421052631579, 7.402597402597403, 4.256410256410256, 24.20253164556962, 23.15, 12.962962962962964, 13.378048780487806, 10.156626506024097, 14.80952380952381, 9.694117647058823, 9.906976744186046, 6.022988505747127, 3.465909090909091, 4.224719101123595, 5.788888888888889, 3.5604395604395602, 4.510869565217392, 2.5376344086021505, 7.76595744680851, 19.852631578947367, 12.645833333333334, 3.2268041237113403, 12.112244897959183, 6.848484848484849, 16.34, 7.027272727272727, 2.5833333333333335, 2.7, 4.485714285714286, 4.286666666666667, 8.9625, 6.911764705882353, 9.938888888888888, 5.868421052631579, 5.965, 2.742857142857143, 2.9045454545454548, 10.217391304347826, 9.2875, 5.676, 5.469230769230769, 11.744444444444444, 9.735714285714286, 1.986206896551724, 7.413333333333333, 4.358064516129033, 4.5, 2.327272727272727, 5.91764705882353, 1.7, 3.013888888888889, 5.8, 2.831578947368421, 8.225641025641025, 10.2625, 10.021951219512195, 4.738095238095238, 2.1, 3.3363636363636364, 8.566666666666666, 3.0391304347826087, 7.793617021276596, 2.3875, 3.048979591836735, 3.428]
    data2 = [0.0, 11.11111111111111, 20.0, 42.857142857142854, 13.636363636363637, 46.34146341463415, 11.11111111111111, 17.647058823529413, 13.924050632911392, 23.45679012345679, 19.047619047619047, 22.699386503067483, 10.619469026548673, 21.45748987854251, 28.205128205128204, 14.613180515759312, 9.223300970873787, 5.708245243128964, 17.02127659574468, 11.524163568773234, 11.683848797250858, 14.566284779050736, 15.2073732718894, 16.61807580174927, 11.989459815546772, 9.622411693057247, 10.081112398609502, 16.55011655011655, 17.02127659574468, 10.497237569060774, 6.47010647010647, 3.7805782060785766, 8.774474256707759, 7.599193006052454, 6.316447779862414, 7.655502392344498, 5.79064587973274, 8.991825613079019, 8.921161825726141, 6.589147286821706, 7.226107226107226, 6.241699867197875, 12.309074573225516, 6.51372388365424, 5.965463108320251, 15.798180314309347, 5.454545454545454, 7.526881720430108, 10.477548111190307, 5.297795327410332, 7.003891050583658, 6.382978723404255, 7.394906413010125, 5.975861053871062, 6.444188722669735, 10.981308411214954, 7.025246981339188, 9.469074986316366, 8.008429926238145, 10.062893081761006, 5.937423010593743, 8.108108108108109, 3.258375401560349, 7.1262226362366095, 5.2631578947368425, 8.254397834912043, 5.28577567683713, 6.5416577881951845, 5.590062111801243, 7.549120992761117, 4.55711185638193, 6.951871657754011, 4.20613868889731, 5.5607917059377945, 5.633802816901408, 7.327905255366395, 10.013052396046989, 6.571936056838366, 9.006433166547534, 4.995766299745978, 5.917955615332885, 4.081964547080826, 5.058994666235655, 5.24637218944347, 7.389004648180798, 3.0303030303030303, 4.1981274539414075, 5.548854041013269, 5.419450631031923, 4.7272727272727275, 3.5314139838320804, 3.45309660282399, 5.366676032593425, 4.553583711652222, 9.06515580736544, 4.669887278582931, 3.4166775755989005, 3.936598674808367, 4.6782114241406045, 5.3984575835475574, 2.1789979071771515, 8.991825613079019, 5.1199604254266635, 5.794070611391315, 5.377906976744186, 4.401471111638391, 5.637982195845697, 4.6389954656435295, 5.617455896007428, 3.3243486073674755, 2.3778071334214004, 4.653751948341126, 3.350739773716275, 4.654965660089393, 3.411513859275053, 6.118029236599892, 4.3423271500843175, 4.155817102385168, 3.999243641864423, 5.152471083070452, 3.2073674182280087, 3.001765744555621, 3.842159916926272, 5.841106039558113, 3.1929100400631296, 2.0523868919378616, 3.0871900602246214, 2.9601029601029603, 5.12615138165799, 4.201203050253398, 2.104235106099618, 1.664760452408184, 3.105538829545923, 2.766798418972332, 3.120345262193026, 2.8126606447822575, 3.155123964002419, 3.4161811851494366, 2.0508937683115516, 1.7973596309845714, 3.1411157993436474, 3.4944600024351637, 3.596270534260767, 3.8781163434903045, 1.5730090317621543, 3.126356925749023, 3.925173874810137, 2.6984004724126422, 1.7546472091926637, 1.5473887814313345, 3.542103108671049, 1.0170581077668344, 1.134958984155523, 2.3951562639123853, 1.8506479434837255, 3.057368601855033, 3.338465107450914, 2.743244631665468]
    # Apply moving average smoothing
    window_size = 20
    smoothed_data1 = np.convolve(data1, np.ones(window_size) / window_size, mode='valid')
    smoothed_data2 = np.convolve(data2, np.ones(window_size) / window_size, mode='valid')
    smoothed_x = x[(window_size - 1) // 2: -(window_size - 1) // 2]  # Adjust x values accordingly

    # Plot the original and smoothed data
    plt.plot(smoothed_x, smoothed_data1, label='Bilateral offsetting execution times', color='blue')
    plt.plot(smoothed_x, smoothed_data2, label='Multilateral offsetting execution times', color='red')

    # Add labels and legend
    plt.xlabel('Payment Volume')
    plt.ylabel('Execution Time (seconds)')
    plt.title('Impact of Payment Volume on Execution Time')
    plt.legend()
    plt.savefig('offsetting_execution_times.png')
    # Show plot
    plt.show()

measure_execution_time()