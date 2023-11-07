class Transaction:
    def __init__(self, sending_bank_id, receiving_bank_id, amount):
        self.sending_bank_id = sending_bank_id
        self.receiving_bank_id = receiving_bank_id
        self.amount = amount


class DatedTransaction(Transaction):
    def __init__(self, sending_bank_id, receiving_bank_id, amount, time):
        super().__init__(sending_bank_id, receiving_bank_id, amount)
        self.time = time
