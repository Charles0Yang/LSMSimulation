class Transaction:
    def __init__(self, time, sending_bank_id, receiving_bank_id, amount):
        self.time = time
        self.sending_bank_id = sending_bank_id
        self.receiving_bank_id = receiving_bank_id
        self.amount = amount
