from datetime import datetime, timedelta
from queue import Queue

import gymnasium as gym
import numpy as np
import pandas as pd
from gymnasium import spaces
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.callbacks import BaseCallback

from src.classes.configs.data_generation_config import DataGenerationConfig
from src.classes.transaction import DatedTransaction
from src.data_scripts.basic_generation import generate_data

MAX_TRANSACTIONS_QUEUED = 30
INITIAL_LIQUIDITY = float(1000)
DELAY_PENALTY = 0.2
FIXED_REWARD = 2
DELAY_TIME = 36000000 # seconds
END_TIME = datetime(2023, 1, 1, 18, 20)


class ActionDistributionCallback(BaseCallback):
    def __init__(self, verbose=0):
        super(ActionDistributionCallback, self).__init__(verbose)

    def _on_step(self) -> bool:
        action_distribution = np.array(self.model.predict(self.model.observation_space.sample())[0])
        self.logger.record('train/action_distribution', action_distribution.mean())
        return True

class BankEnv(gym.Env):

    def __init__(self):
        super(BankEnv, self).__init__()

        self.action_space = spaces.Discrete(2)
        self.observation_space = spaces.Box(low=0, high=np.inf, shape=(2,), dtype=np.float64)
        self.current_liquidity = INITIAL_LIQUIDITY
        self.min_liquidity = INITIAL_LIQUIDITY
        self.transactions_queue = Queue()
        self.transactions = self.get_transactions()
        self.id = 0
        self.time = self.transactions[0]
        self.done = False

    def step(self, action):

        # Process delayed transactions
        # Get transactions to send at the time
            # Decide whether to send or postpone
        # Calculate reward
        # Find next transaction to send
        # Calculate how much received in that period

        # Define reward as:
        # If we go below our min liquidity reward is -amount_below_previous_min
        # If we don't go below our min liquidity reward is some fixed constant - no delay reward
        # If we postpone our transaction our reward is delay_penalty * transaction_amount then we re-insert the transaction into the queue

        # When delay a transaction we just take off the delay penalty until we receive an incoming transaction
        start_step_time = self.time
        transaction_amount = 0
        receiving_amount = 0
        reward = 0
        while self.transactions and self.transactions[0].time == self.time:
            transaction = self.transactions[0]
            self.transactions = self.transactions[1:]
            if transaction.sending_bank_id == self.id:
                transaction_amount = transaction.amount
                if action == 0:  # Send through the payment
                    self.current_liquidity -= transaction.amount
                    if self.current_liquidity < self.min_liquidity:
                        reward = self.current_liquidity - self.min_liquidity
                        self.min_liquidity = self.current_liquidity
                    else:
                        reward = FIXED_REWARD
                else:
                    reward = -transaction.amount * 0.2
                    transaction.time += timedelta(seconds=DELAY_TIME)
                    for i in range(len(self.transactions)):
                        if transaction.time <= self.transactions[i].time:
                            self.transactions.insert(i, transaction)
                            break

        observation = np.array([self.current_liquidity, transaction_amount])
        liquidity_after = self.current_liquidity

        next_sending_time = END_TIME
        for transaction in self.transactions:
            if transaction.time < END_TIME:
                if transaction.sending_bank_id == self.id:
                    next_sending_time = transaction.time
                    break
                else:
                    if transaction.receiving_bank_id == self.id:
                        receiving_amount += transaction.amount
                    self.transactions = self.transactions[1:]

        self.time = next_sending_time
        if self.time >= END_TIME:
            self.done = True

        if self.done:
            reward = 0
            for transaction in self.transactions:
                reward -= transaction.amount

        self.current_liquidity += receiving_amount

        if len(self.transactions) == 0:
            next_transaction = "None"
        else:
            next_transaction = self.transactions[0]
        info = {
        }

        return observation, reward, self.done, False, info

    def reset(self, seed=None):
        self.current_liquidity = INITIAL_LIQUIDITY
        self.previous_liquidity = INITIAL_LIQUIDITY
        self.min_liquidity = INITIAL_LIQUIDITY
        self.transactions_queue = Queue()
        self.done = False
        self.transactions = self.get_transactions()
        self.time = self.transactions[0].time

        observation = np.array([INITIAL_LIQUIDITY, 0])
        info = {}
        return observation, info

    def get_transactions(self):
        data_generation_config = DataGenerationConfig(
            num_banks=2,
            num_transactions=4000,
            min_transaction_amount=5,
            max_transaction_amount=20
        )
        #generate_data(data_generation_config)
        df = pd.read_csv(f"/Users/cyang/PycharmProjects/PartIIProject/data/synthetic_data/rl/random_data.csv")
        transactions_to_do = df.values.tolist()
        transactions = []
        for row in transactions_to_do:
            time = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
            sending_bank_id = int(row[1])
            receiving_bank_id = int(row[2])
            amount = float(row[3])
            priority = int(row[4])

            transaction = DatedTransaction(sending_bank_id, receiving_bank_id, amount, time, priority)
            transactions.append(transaction)
        return transactions


env = BankEnv()
episodes = 1

def test(env, episodes):
    for episode in range(episodes):
        done = False
        obs = env.reset()
        while not done:
            random_action = env.action_space.sample()
            obs, reward, done, truncated, info = env.step(random_action)
            print(f"{info['time']}: {info['current_liquidity']}, action: {random_action}, reward: {reward}")


logdir = "./ppo_tensorboard"

model = PPO('MlpPolicy', env, verbose=1,
            tensorboard_log=logdir, learning_rate=0.0001)  # python3 -m tensorboard.main --logdir=./ppo_tensorboard
model.learn(total_timesteps=400000, callback=ActionDistributionCallback())
obs = model.env.observation_space.sample()

