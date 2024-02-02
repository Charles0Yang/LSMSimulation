from src.data_scripts.basic_generation import generate_data
from src.metrics import Metrics
from src.simulation import settings
from src.simulation.day_simulator import simulate_day_transactions
from src.simulation.setup import generate_banks
import numpy as np


# Goal of this class is to take in configs and number of days to run simulator then return relevant metrics
class MultipleSimulator:

    def __init__(self):
        self.data_generation_config = settings.data_generation_config
        self.day_config = settings.day_config
        self.csv_settings = settings.csv_settings
        self.num_passes = settings.num_passes
        self.banks = generate_banks(settings.day_config.bank_types,
                                    settings.day_config.starting_balance,
                                    settings.csv_settings.input_file_name)
        self.all_normal_banks = generate_banks(settings.day_config_benchmark.bank_types,
                                               settings.day_config.starting_balance,
                                               settings.csv_settings.input_file_name)
        self.metrics = []

    def one_pass_full_run(self):
        if settings.generate_new_data:
            generate_data(settings.data_generation_config)
        metrics = Metrics()
        banks, collected_metrics = simulate_day_transactions(self.banks, metrics)
        self.metrics.append(collected_metrics)
        return banks

    def multiple_run(self):
        for _ in range(self.num_passes):
            banks = simulate_day_transactions(self.banks)
        return self.collect_metrics(banks)

    def compare_delay_behaviour(self):
        if settings.generate_new_data:
            generate_data(settings.data_generation_config)

        metrics = Metrics()
        original_banks, collected_metrics = simulate_day_transactions(self.banks, metrics)
        for i in range(3, len(original_banks)):
            print(f"Bank {original_banks[i].name} delayed {original_banks[i].calculate_percentage_transactions_delayed() * 100:.2f}% of transactions")

        for i in range(3, len(original_banks)):
            print(f"Bank {original_banks[i].name} delayed {original_banks[i].calculate_average_delay_per_transaction():.2f} minutes per transaction on average")
        metrics = Metrics()
        normal_banks, collected_metrics = simulate_day_transactions(self.all_normal_banks, metrics)

        delay_min_balances = [original_banks[bank].min_balance for bank in original_banks]
        no_delay_min_balances = [normal_banks[bank].min_balance for bank in normal_banks]
        bank_balances = list(zip(delay_min_balances, no_delay_min_balances))

        print(no_delay_min_balances)
        print(delay_min_balances)

        for bank in original_banks:
            difference_from_delaying = (bank_balances[bank][0] - bank_balances[bank][1]) / bank_balances[bank][1]
            if difference_from_delaying >= 0:
                print(f"Bank {original_banks[bank].name} benefited {difference_from_delaying * 100:.2f}% in min liquidity from banks delaying")
            else:
                print(f"Bank {original_banks[bank].name} lost {difference_from_delaying * 100:.2f}% in min liquidity from banks delaying")


    def calc_average_min_balance(self, banks):
        total_min_balance = 0
        for bank in banks:
            total_min_balance += banks[bank].min_balance

        return total_min_balance / (len(banks.keys()))

    def calc_average_settlement_delay(self, banks):
        total_settlement_delay = 0
        for bank in banks:
            total_settlement_delay += banks[bank].cum_settlement_delay

        return total_settlement_delay / (len(banks.keys()) * 360)  # Calculate in hours

    def collect_metrics(self, banks):
        metrics = [
            self.calc_average_min_balance(banks),
            self.calc_average_settlement_delay(banks)
        ]
        return metrics
