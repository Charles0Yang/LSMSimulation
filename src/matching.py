from src.classes.transaction import Transaction


def naive_bilateral_matching(banks, transactionQueue, timestep):


    send_receive_pairs = {}
    while not transactionQueue.empty():
        transaction = transactionQueue.get()
        send_receive_pair = (banks[transaction.sending_bank_id], banks[transaction.receiving_bank_id])
        reverse_pair = (banks[transaction.receiving_bank_id], banks[transaction.sending_bank_id])

        if send_receive_pair in send_receive_pairs:
            send_receive_pairs[send_receive_pair] += transaction.amount

        elif reverse_pair in send_receive_pairs:
            send_receive_pairs[reverse_pair] -= transaction.amount

        else:
            send_receive_pairs[send_receive_pair] = transaction.amount

    for pair in send_receive_pairs:
        amount = send_receive_pairs[pair]
        sending_bank, receiving_bank = pair

        transaction = Transaction(timestep, sending_bank.id, receiving_bank.id, amount)

        sending_bank.outbound_transaction(transaction)
        receiving_bank.inbound_transaction(transaction)



