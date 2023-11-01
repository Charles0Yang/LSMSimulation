from src.classes.transaction import Transaction

class Bank:
    def __init__(self, id, name, balance):
        self.id = id
        self.name = name
        self.balance = balance
        self.min_balance = 100000000
        self.transactions = []
    def inbound_transaction(self, transaction: Transaction):
        self.balance += transaction.amount
        self.transactions.append(transaction)
        self.check_min_balance()

    def outbound_transaction(self, transaction: Transaction):
        self.balance -= transaction.amount
        self.transactions.append(transaction)
        self.check_min_balance()

    def check_min_balance(self):
        if self.balance < self.min_balance:
            self.min_balance = self.balance




