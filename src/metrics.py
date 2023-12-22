class Metrics:

    def __init__(self):
        self.liquidity_used = 0
        self.total_transaction_volume = 0
        self.liquidity_saved_ratio = 0
        self.offset_ratio = 0

    def add_to_liquidity_and_transaction_volumes(self, balances_before, balances_after, transactions):
        for before, after in zip(balances_before, balances_after):
            self.liquidity_used += max(0, before-after)
        self.total_transaction_volume += sum([transaction.amount for transaction in transactions])

    def calculate_liquidity_saved_ratio(self):
        self.liquidity_saved_ratio = ((self.total_transaction_volume - self.liquidity_used) / self.total_transaction_volume)

