from src.data_scripts.basic_generation import generate_data
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

    def one_pass_full_run(self):
        if settings.generate_new_data:
            generate_data(settings.data_generation_config)
        banks = simulate_day_transactions(self.banks)
        return banks

    def multiple_run(self):
        for _ in range(self.num_passes):
            banks = simulate_day_transactions(self.banks)
        return self.collect_metrics(banks)

    def compare_delay_behaviour(self):
        original_banks = simulate_day_transactions(self.banks)
        print([original_banks[bank].min_balance for bank in original_banks])

        normal_banks = simulate_day_transactions(self.all_normal_banks)
        print([normal_banks[bank].min_balance for bank in normal_banks])

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
