from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, HourLocator
import sys


def plot(file_name):
    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']

    df = pd.read_csv(f"/Users/cyang/PycharmProjects/PartIIProject/src/data/synthetic_data/{file_name}")
    df["time"] = pd.to_datetime(df["time"])
    times = df["time"]

    plt.figure(figsize=(10, 6))
    ax = plt.gca()

    for i, col in enumerate(df.columns[1:]):
        balances = df[col]
        color = colors[i % len(colors)]
        ax.plot(times, balances, linestyle='-', color=color, label=str(col))

    date_format = DateFormatter("%H:%M")
    ax.xaxis.set_major_formatter(date_format)
    ax.xaxis.set_major_locator(HourLocator(interval=1))

    plt.xlabel("Time")
    plt.ylabel("Balance")

    ax.legend()

    plt.show()
