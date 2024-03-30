import copy
from datetime import datetime

import numpy as np

from src.classes.configs.csv_config import CSVSettings
from src.classes.configs.data_generation_config import DataGenerationConfig
from src.classes.configs.day_config import DayConfig

generate_new_data = True

start_time = datetime(2023, 1, 1, 5, 45)
end_time = datetime(2023, 1, 1, 18, 20)

delay_amount = 1800  # In seconds
priority_transaction_percentage = 0.2
priority_balance_percentage = 0.8

num_passes = 1

data_generation_config = DataGenerationConfig(
    num_banks=5,
    num_transactions=5000,
    min_transaction_amount=1,
    max_transaction_amount=20
)

day_config = DayConfig(
    num_banks=data_generation_config.num_banks,
    bank_types=[3, 0, 0, 2],
    starting_balance=1000,
    LSM_enabled=True,
    matching_window=120,
)

day_config_benchmark = copy.copy(day_config)
day_config_benchmark.bank_types = [5, 0, 0, 0]

csv_settings = CSVSettings(
    input_file_name='random/random_data.csv',
    output_file_name='random/random_output.csv',
    headers=['time'] + list(np.arange(day_config.num_banks))
)
