# Exploring the Bank of England's Liquidity Saving Mechanism Algorithms

This project aims to provide a simulator for CHAPS that can be used to test different system configurations and the impacts of bilateral and mulitlateral offsetting algorithms on useful metrics from the Bank of England's and individuals DPs point of view.

## Table of Contents

- [Introduction](#introduction)
- [Installation](#installation)
- [Usage](#usage)
  - [Generating Synthetic Datasets](#generating-synthetic-datasets)
  - [Running the Main Simulator](#running-the-main-simulator)
  - [Running the RL Environment Test Environment](#running-the-rl-environment-test-environment)
- [License](#license)

## Introduction

There are a few different components to this repository.
- Synthetic Data Generation
- Running the Simulator
- Training the RL agents

## Installation

To install the project and its dependencies, follow these steps:

1. **Clone the repository**:
   - `git clone https://github.com/Charles0Yang/LSMSimulation`

2. **Navigate to the project directory**

3. **Create a virtual environment** (optional but recommended):
   - `python -m venv venv`

4. **Activate the virtual environment**:
   - On Windows:
     - `venv\Scripts\activate`
   - On macOS and Linux:
     - `source venv/bin/activate`

5. **Install the project dependencies**:
   - `pip install -r requirements.txt`

   This command will install all the required Python packages listed in the `requirements.txt` file.

## Usage


### Generating Synthetic Datasets

The generation of synthetic datasets is done in `src/data_scripts/basic_generation.py`.
This can be run individually by specifiying the data generation config, and providing this to the `generateData` function.

### Running Simulations

Simulations can be run using the provided functions in `src/simulation/multiple_simulator.py`.
These perform a variety of different functions, from assessing the impacts of delay DPs to just running a full pas provided a day config.
The settings for the simulations can be found in `src/simulation/settings.py` which defines multiple parameters necessary for the simulation.

### Training the RL Agent

This is done in `src/rl/bankenv.py`. Fixed parameters such as the fixed reward and delay penalty can be defined for each run.

### License
MIT License

Copyright (c) [2024] [Charles Yang]