import pandas as pd
import matplotlib.pyplot as plt
import sys

file = sys.argv[1]
colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']

df = pd.read_csv(f"../data/synthetic_data/{file}")
time = df["time"]

plt.figure(figsize=(10, 6))
for i, col in enumerate(df.columns[1:]):
    balances = df[col]
    color = colors[i % len(colors)]
    plt.plot(time, balances, linestyle='-', color=color)

plt.xlabel("Time")
plt.ylabel("Balance")

plt.show()

