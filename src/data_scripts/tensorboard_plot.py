import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import ticker


def plot_learning_rate():
    # Read the first CSV file into a DataFrame
    df1 = pd.read_csv('data/lsm/PPO_1.csv')

    # Read the second CSV file into a DataFrame
    df2 = pd.read_csv('data/lsm/PPO_2.csv')

    df3 = pd.read_csv('data/lsm/PPO_3.csv')

    # Extract data from both DataFrames
    steps1 = df1['Step']
    values1 = df1['Value']

    steps2 = df2['Step']
    values2 = df2['Value']

    steps3 = df3['Step']
    values3 = df3['Value']

    # Plot data from the first file
    plt.plot(steps1, values1, label='Learning Rate = 0.00015')

    # Plot data from the second file
    plt.plot(steps2, values2, label='Learning Rate = 0.00025')

    plt.plot(steps3, values3, label='Learning Rate = 0.0005')

    plt.xlabel('Episode')
    plt.ylabel('Reward')
    plt.title('Average Reward per Episode')
    plt.legend()
    plt.show()

def plot_RL_algorithms():
    # Read the first CSV file into a DataFrame
    df1 = pd.read_csv('data/lsm/A2C_1.csv')

    # Read the second CSV file into a DataFrame
    df2 = pd.read_csv('data/lsm/DQN_2.csv')

    df3 = pd.read_csv('data/lsm/PPO_2.csv')

    # Extract data from both DataFrames
    steps1 = df1['Step']
    values1 = df1['Value']

    steps2 = df2['Step']
    values2 = df2['Value']

    steps3 = df3['Step']
    values3 = df3['Value']

    # Plot data from the first file
    plt.plot(steps1, values1, label='A2C')

    # Plot data from the second file
    plt.plot(steps2, values2, label='DQN')

    plt.plot(steps3, values3, label='PPO')

    plt.xlabel('Episode')
    plt.ylabel('Reward')
    plt.title('Average Reward per Episode')
    plt.legend()
    plt.show()

def plot_0_delay():
    # Read the first CSV file into a DataFrame
    df1 = pd.read_csv('data/lsm/PPO_43.csv') # FR = 0, LSM = 0
    df2 = pd.read_csv('data/lsm/PPO_57.csv') # FR = 0, LSM = 1
    df3 = pd.read_csv('data/lsm/PPO_58.csv') # FR = 1, LSM = 0
    df4 = pd.read_csv('data/lsm/PPO_59.csv') # FR = 1, LSM = 1

    # Extract data from both DataFrames
    time1 = df1['Step']
    data_series1 = df1['Value']
    time2 = df2['Step']
    data_series2 = df2['Value']
    time3 = df3['Step']
    data_series3 = df3['Value']
    time4 = df4['Step']
    data_series4 = df4['Value']

    def moving_average(data, window_size):
        """Compute moving average of data."""
        return data.rolling(window=window_size, min_periods=1).mean()

    window_size = 100 # Adjust the window size as needed
    smoothed_data1 = moving_average(data_series1, window_size)
    smoothed_data2 = moving_average(data_series2, window_size)
    smoothed_data3 = moving_average(data_series3, window_size)
    smoothed_data4 = moving_average(data_series4, window_size)

    # Plotting
    plt.plot(time3[:-1], smoothed_data3[:-1], label='FR = 0, LSM = 0', color='purple', linestyle='-')
    plt.plot(time4[:-1], smoothed_data4[:-1], label='FR = 0, LSM = 1', color='orange', linestyle='-')
    plt.plot(time1[:-1], smoothed_data1[:-1], label='FR = 1, LSM = 0', color='purple', linestyle=':')
    plt.plot(time2[:-1], smoothed_data2[:-1], label='FR = 1, LSM = 1', color='orange', linestyle=':')

    plt.scatter(time1[len(time1)-1], smoothed_data1[len(smoothed_data1)-1], color='purple')
    plt.scatter(time2[len(time2)-1], smoothed_data2[len(smoothed_data2)-1], color='orange')
    plt.scatter(time3[len(time3)-1], smoothed_data3[len(smoothed_data3)-1], color='purple')
    plt.scatter(time4[len(time4)-1], smoothed_data4[len(smoothed_data4)-1], color='orange')

    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: '{:.0f}'.format(x)))
    plt.xlabel('Timesteps')
    plt.ylabel('Reward')
    #plt.ylim(0, 1)
    plt.legend(loc='upper left')
    plt.tight_layout()  # Adjust layout to prevent labels from being cut off
    plt.savefig('LSM_delay_rl.png')
    plt.show()


plot_0_delay()