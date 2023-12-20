from src.data_scripts.plotter import plot_from_file
from src.simulation import settings
from src.simulation.multiple_simulator import MultipleSimulator

if __name__ == '__main__':

    lsm_random_metrics = MultipleSimulator()
    print(f"LSM Random avg min balance: {lsm_random_metrics.compare_delay_behaviour()}")

    plot_from_file(settings.csv_settings.output_file_name)