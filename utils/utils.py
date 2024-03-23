from collections import deque, namedtuple
import yfinance as yf
import pandas as pd
import torch
import random
import matplotlib.pyplot as plt

class ExperienceReplay(object):
    def __init__(self, buffer_size: int = 10000, device: str = None):
        self.buffer = deque([], maxlen=buffer_size)
        self.transition = namedtuple('Experience', ('state', 'action', 'next_state', 'reward'))

        if device is not None:
            self.device = torch.device(device)
        else:
            self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

    def add_experience(self, *args):
        """Adds an experience to the replay buffer."""
        self.buffer.append(self.transition(*args))

    def sample(self, batch_size: int = 32, separate: bool = True) -> tuple:
        """Samples a batch of experiences from the replay buffer."""
        samples = random.sample(self.buffer, k=batch_size)
        if separate:
            return self.transition(*zip(*samples))
        else:
            return samples

    def __len__(self):
        """Gets length of the replay buffer."""
        return len(self.buffer)


class Config(object):
    """
    Configuration object for running experiments. 
    
    Edit to add useful features.
    """
    def __init__(self):
        self.environment = None
        self.GPU = False
        self.hyperparameters = None


class DataDownloader:
    """Class for downloading data from Yahoo Finance."""
    def __init__(
            self,
            start_date: str,
            end_date: str,
            tickers: list
    ):
        """
        Args:
        - start_date (str): Start date for data download.
        - end_date (str): End date for data download.
        - tickers (list): List of tickers to download data for.
        """
        self.start_date = start_date
        self.end_date = end_date
        self.tickers = tickers

    def download_data(self) -> pd.DataFrame:
        """
        Downloads data from Yahoo Finance.

        Returns:
            pd.DataFrame: DataFrame containing the close prices for the specified tickers.
        """
        data = yf.download(self.tickers, start=self.start_date, end=self.end_date)
        return data
    

def split_data(data: pd.DataFrame, split_date: str) -> tuple:
    """
    Splits the data into training and testing sets.

    Args:
    - data (pd.DataFrame): DataFrame containing the data to split.
    - split_date (str): Date to split the data on.

    Returns:
    - tuple: Training and testing sets.
    """
    data.set_index('Date', inplace=True)

    train = data[data.index < split_date]
    test = data[data.index >= split_date]

    return train, test


def plot_portfolio(data: pd.DataFrame, actions: list, initial_balance: int = 1000):
    """
    Plots the portfolio balance over time.

    Args:
    - data (pd.DataFrame): DataFrame containing the data to plot.
    - actions (list): List of actions taken by the agent.
    - initial_balance (int): Initial balance for the portfolio.
    """
    
    portfolio_value = [initial_balance]
    own_share = False
    num_shares = 0

    close_prices = data['Close'].values

    # assert len(actions) == len(close_prices), 'Length of actions and close prices must be the same.'
    # print(len(actions), len(close_prices))

    # Iterate through list of actions and update portfolio value
    for i, action in enumerate(actions):

        # If action == buy and no shares owned, buy shares
        if action == 0 and num_shares == 0:
            own_share = True
            num_shares = portfolio_value[-1] / close_prices[i]
            
            if i < len(actions) - 1:
                portfolio_value.append(num_shares * close_prices[i+1])

        # If action == sell and shares owned, sell shares
        elif action == 2 and num_shares > 0:
            own_share = False
            portfolio_value.append(num_shares * close_prices[i])
            num_shares = 0

        # If action in [buy, hold] and shares owned, update portfolio value
        elif (action == 0 or action == 1) and num_shares > 0:
            if i < len(actions) - 1:
                portfolio_value.append(num_shares * close_prices[i+1])
        
        # If action in [sell, hold] and no shares owned, hold cash
        elif (action == 2 or action == 1) and num_shares == 0:
            portfolio_value.append(portfolio_value[-1])

    plt.plot(portfolio_value)
    plt.show()

    return portfolio_value




