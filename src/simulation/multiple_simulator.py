from src.data_scripts.basic_generation import generate_data
from src.simulation.day_simulator import simulate_day_transactions
from src.simulation.setup import generate_banks


# Goal of this class is to take in configs and number of days to run simulator then return relevant metrics
class MultipleSimulator:

    def __init__(self, data_generation_config, day_config, csv_settings, num_passes):
        self.data_generation_config = data_generation_config
        self.day_config = day_config
        self.csv_settings = csv_settings
        self.num_passes = num_passes
        self.banks = generate_banks(day_config.bank_types, day_config.starting_balance,
                               csv_settings.input_file_name)

    def one_pass_full_run_new_data(self):
        generate_data(self.data_generation_config)
        banks = simulate_day_transactions(self.banks, self.day_config, self.csv_settings, self.banks)
        return banks

    def one_pass_full_run_same_data(self):
        banks = simulate_day_transactions(self.day_config, self.csv_settings, self.banks)
        return banks

    def multiple_run(self):
        for _ in range(self.num_passes):
            banks = simulate_day_transactions(self.day_config, self.csv_settings, self.banks)
        return self.collect_metrics(banks)

    def calc_average_min_balance(self, banks):
        total_min_balance = 0
        for bank in banks:
            total_min_balance += banks[bank].min_balance

        return total_min_balance / (len(banks.keys()))

    def calc_average_settlement_delay(self, banks):
        total_settlement_delay = 0
        for bank in banks:
            total_settlement_delay += banks[bank].cum_settlement_delay

        return total_settlement_delay / (len(banks.keys()) * 360) # Calculate in hours

    def collect_metrics(self, banks):
        metrics = [
            self.calc_average_min_balance(banks),
            self.calc_average_settlement_delay(banks)
        ]
        return metrics