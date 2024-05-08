class Transaction:
    def __init__(self, sending_bank_id, receiving_bank_id, amount, priority):
        self.sending_bank_id = sending_bank_id
        self.receiving_bank_id = receiving_bank_id
        self.amount = amount
        self.priority = priority # 0 priority for non-urgent, 1 priority for urgennt

class DatedTransaction(Transaction):
    def __init__(self, sending_bank_id, receiving_bank_id, amount, time, priority):
        super().__init__(sending_bank_id, receiving_bank_id, amount, priority)
        self.time = time

    def __repr__(self):
        return f"({self.sending_bank_id},{self.receiving_bank_id}): {self.amount}"

    def __lt__(self, other):
        return self.time < other.time