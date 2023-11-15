import numpy as np

from src.classes.configs.csv_config import CSVSettings
from src.classes.configs.data_generation_config import DataGenerationConfig
from src.classes.configs.day_config import DayConfig
from src.data_scripts.plotter import plot
from src.test_suite import MetricGetter

if __name__ == '__main__':

    num_passes = 1

    data_generation_config = DataGenerationConfig(
        num_banks=5,
        num_transactions=1000,
        min_transaction_amount=10,
        max_transaction_amount=1
    )

    lsm_day_config = DayConfig(
        num_banks=data_generation_config.num_banks,
        bank_types=[3, 2],
        starting_balance=500,
        LSM_enabled=True,
        matching_window=30,
        timesteps=300
    )

    no_lsm_day_config = DayConfig(
        num_banks=data_generation_config.num_banks,
        bank_types=[3, 2],
        starting_balance=500,
        LSM_enabled=False,
        matching_window=1,
        timesteps=300
    )

    random_csv_settings = CSVSettings(
        input_file_name='random/random_data.csv',
        output_file_name='random/random_output.csv',
        headers=['time'] + list(np.arange(lsm_day_config.num_banks))
    )

    random_metrics = MetricGetter(data_generation_config, lsm_day_config, random_csv_settings, num_passes)

    print(f"No LSM Random avg min balance: {random_metrics.calc_average_min_balance()}")

    plot(random_csv_settings.output_file_name)