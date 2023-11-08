from src.data_scripts.basic_generation import generate_data
from src.simulator import simulate_day_transactions


class MetricGetter:

    def __init__(self, data_generation_config, day_config, csv_settings, num_passes):
        self.data_generation_config = data_generation_config
        self.day_config = day_config
        self.csv_settings = csv_settings
        self.num_passes = num_passes

    def one_pass_full_run_new_data(self):
        generate_data(self.data_generation_config)
        banks = simulate_day_transactions(self.day_config, self.csv_settings)
        return banks

    def one_pass_full_run_same_data(self):
        banks = simulate_day_transactions(self.day_config, self.csv_settings)
        return banks

    def calc_average_min_balance(self):
        average_min_balance = 0
        for _ in range(self.num_passes):
            banks = self.one_pass_full_run_same_data()
            for bank in banks:
                average_min_balance += banks[bank].min_balance

        return average_min_balance / (len(banks.keys()) * self.num_passes)
