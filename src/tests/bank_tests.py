from src.classes.bank import DelayWhenConvenientBank, NormalBank
from src.simulation.metrics import Metrics
from src.simulation.day_simulator import simulate_day_transactions


def weird_test():
    banks = {0: NormalBank(0, 'A', 30, "test/bank_test.csv"),
             1: DelayWhenConvenientBank(1, 'B', 30, "test/bank_test.csv", 30)
             }

    metrics = Metrics()
    simulate_day_transactions(banks, metrics)


def execute_tests():
    weird_test()


execute_tests()
