class DayConfig:
    def __init__(self, num_banks, starting_balance, LSM_enabled, matching_window, timesteps):
        self.num_banks = num_banks
        self.starting_balance = starting_balance
        self.LSM_enabled = LSM_enabled
        self.matching_window = matching_window
        self.timesteps = timesteps
