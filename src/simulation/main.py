from src.data_scripts.plotter import plot_from_file
from src.simulation import settings
from src.simulation.multiple_simulator import MultipleSimulator
import resource

if __name__ == '__main__':

    lsm_random_metrics = MultipleSimulator()
    lsm_random_metrics.compare_delay_behaviour()

    plot_from_file(settings.csv_settings.output_file_name)
    #print(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    #plot_from_file("../../data/synthetic_data/rl/random_data.csv")