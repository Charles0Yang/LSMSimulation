import numpy as np

from src.classes.csv_settings import CSVSettings
from src.classes.day_config import DayConfig
from src.simulator import simulate_day_transactions

if __name__ == '__main__':

    day_config = DayConfig(
        num_banks=5,
        starting_balance=500,
        LSM_enabled=True,
        matching_window=20,
        timesteps=1000
    )

    csv_settings = CSVSettings(
        input_file_name='alternative/alternative_data.csv',
        output_file_name='alternative/alternative_output.csv',
        headers=list(np.arange(day_config.num_banks))
    )

    simulate_day_transactions(day_config, csv_settings)