from src.data_scripts.plotter import plot_from_file
from src.simulation import settings
from src.simulation.multiple_simulator import MultipleSimulator
import resource

lsm_random_metrics = MultipleSimulator()
lsm_random_metrics.compare_characteristic_on_datasets()
