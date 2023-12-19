import numpy as np

from src.classes.configs.csv_config import CSVSettings
from src.classes.configs.data_generation_config import DataGenerationConfig
from src.classes.configs.day_config import DayConfig

delay_amount = 120  # In seconds
num_passes = 1

data_generation_config = DataGenerationConfig(
    num_banks=5,
    num_transactions=5000,
    min_transaction_amount=10,
    max_transaction_amount=20
)

day_config = DayConfig(
    num_banks=data_generation_config.num_banks,
    bank_types=[3, 2],
    starting_balance=500,
    LSM_enabled=True,
    matching_window=240,
    timesteps=300
)

csv_settings = CSVSettings(
    input_file_name='random/random_data.csv',
    output_file_name='random/random_output.csv',
    headers=['time'] + list(np.arange(day_config.num_banks))
)
