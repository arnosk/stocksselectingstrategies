"""3: Quantitative Value Strategy

Original from:
https://github.com/nickmccullum/algorithmic-trading-python/blob/master/finished_files/003_quantitative_value_strategy.ipynb

"Value investing" means investing in the stocks that are cheapest relative to common measures of business value 
(like earnings or assets).
Python script investing strategy that that selects the 50 stocks with the best value metrics. 
From there, we will calculate recommended trades for an equal-weight portfolio of these 50 stocks.

CSV with S&P stocks: (This is OLD)
http://nickmccullum.com/algorithmic-trading-python/sp_500_stocks.csv

Certificate SSL file:
C:\\Users\\i154424\\Documents\\Projects\\test\\stocksdata\\venv\\Lib\\site-packages\\certifi\\cacert.pem

20-12-2022
Arno Kemner
"""

import math
from statistics import mean

import numpy as np  # The Numpy numerical computing library
import pandas as pd  # The Pandas data science library
import requests  # The requests library for HTTP requests in Python
from scipy import stats  # The SciPy stats module

from config import IEX_CLOUD_API_TOKEN
from writerexcel import write_to_excel

# removed some unexisting tickers: DISCA, HFC, VIAC, WLTW
stocks = pd.read_csv('sp_500_stocks.csv')

# symbol = 'AAPL'
# api_url = f'https://sandbox.iexapis.com/stable/stock/{symbol}/quote?token={IEX_CLOUD_API_TOKEN}'
# data = requests.get(api_url).json()
# print(data)


def chunks(lst, n):
    """Yield successive n-sized chunks from lst.

    Function sourced from
    https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


symbol_groups = list(chunks(stocks['Ticker'], 100))
symbol_strings = []
for i in range(0, len(symbol_groups)):
    symbol_strings.append(','.join(symbol_groups[i]))

# Adding Stocks Data to a Pandas DataFrame
# Looping Through Tickers in chunk List of Stocks

"""
Every valuation metric has certain flaws.

For example, the price-to-earnings ratio doesn't work well with stocks with negative earnings.

Similarly, stocks that buyback their own shares are difficult to value using the price-to-book ratio.

Investors typically use a composite basket of valuation metrics to build robust quantitative value strategies. 
In this section, we will filter for stocks with the lowest percentiles on the following metrics:

Price-to-earnings ratio
Price-to-book ratio
Price-to-sales ratio
Enterprise Value divided by Earnings Before Interest, Taxes, Depreciation, and Amortization (EV/EBITDA)
Enterprise Value divided by Gross Profit (EV/GP)

Some of these metrics aren't provided directly by the IEX Cloud API, and must be computed after pulling raw data. 
We'll start by calculating each data point from scratch.

rv often. It stands for robust value
"""
rv_columns = [
    'Ticker',
    'Price',
    'Number of Shares to Buy',
    'Price-to-Earnings Ratio',
    'PE Percentile',
    'Price-to-Book Ratio',
    'PB Percentile',
    'Price-to-Sales Ratio',
    'PS Percentile',
    'EV/EBITDA',
    'EV/EBITDA Percentile',
    'EV/GP',
    'EV/GP Percentile',
    'RV Score'
]

rv_dataframe = pd.DataFrame(columns=rv_columns)

for symbol_string in symbol_strings:
    batch_api_call_url = f'https://sandbox.iexapis.com/stable/stock/market/batch?symbols={symbol_string}&types=quote,advanced-stats&token={IEX_CLOUD_API_TOKEN}'
    data = requests.get(batch_api_call_url).json()
    for symbol in symbol_string.split(','):
        enterprise_value = data[symbol]['advanced-stats']['enterpriseValue']
        ebitda = data[symbol]['advanced-stats']['EBITDA']
        gross_profit = data[symbol]['advanced-stats']['grossProfit']

        try:
            ev_to_ebitda = enterprise_value/ebitda
        except TypeError:
            ev_to_ebitda = np.NaN

        try:
            ev_to_gross_profit = enterprise_value/gross_profit
        except TypeError:
            ev_to_gross_profit = np.NaN

        new_data = pd.DataFrame([[
                                 symbol,
                                 data[symbol]['quote']['latestPrice'],
                                 'N/A',
                                 data[symbol]['quote']['peRatio'],
                                 'N/A',
                                 data[symbol]['advanced-stats']['priceToBook'],
                                 'N/A',
                                 data[symbol]['advanced-stats']['priceToSales'],
                                 'N/A',
                                 ev_to_ebitda,
                                 'N/A',
                                 ev_to_gross_profit,
                                 'N/A',
                                 'N/A'
                                 ]],
                                columns=rv_columns)
        rv_dataframe = pd.concat([rv_dataframe, new_data],
                                 ignore_index=True,
                                 axis=0)

# print(rv_dataframe.columns)
# print(rv_dataframe.all)

# print missing data:
print(rv_dataframe[rv_dataframe.isnull().any(axis=1)])

"""
Dealing with missing data is an important topic in data science.

There are two main approaches:

Drop missing data from the data set (pandas' dropna method is useful here)
Replace missing data with a new value (pandas' fillna method is useful here)
In this tutorial, we will replace missing data with the average non-NaN data point from that column.
"""
for column in ['Price-to-Earnings Ratio', 'Price-to-Book Ratio', 'Price-to-Sales Ratio',  'EV/EBITDA', 'EV/GP']:
    rv_dataframe[column].fillna(rv_dataframe[column].mean(), inplace=True)

# drop rows with None
# rv_dataframe = rv_dataframe.dropna().reset_index()
# rv_dataframe = rv_dataframe.mask(rv_dataframe.eq('None')).dropna().reset_index()


# Calculating Value Percentiles
metrics = {
    'Price-to-Earnings Ratio': 'PE Percentile',
    'Price-to-Book Ratio': 'PB Percentile',
    'Price-to-Sales Ratio': 'PS Percentile',
    'EV/EBITDA': 'EV/EBITDA Percentile',
    'EV/GP': 'EV/GP Percentile'
}

for row in rv_dataframe.index:
    for metric in metrics.keys():
        rv_dataframe.loc[row, metrics[metric]] = stats.percentileofscore(
            rv_dataframe[metric],
            rv_dataframe.loc[row, metric]
        )/100

# Print each percentile score to make sure it was calculated properly
for metric in metrics.values():
    print(rv_dataframe[metric])

# print(rv_dataframe)

# Calculating the RV Score
for row in rv_dataframe.index:
    value_percentiles = []
    for metric in metrics.keys():
        value_percentiles.append(rv_dataframe.loc[row, metrics[metric]])
    rv_dataframe.loc[row, 'RV Score'] = mean(value_percentiles)


# Selecting the 50 Best Value Stocks
rv_dataframe.sort_values(by='RV Score', inplace=True)
rv_dataframe = rv_dataframe[:50]
rv_dataframe.reset_index(drop=True, inplace=True)


# Calculating the Number of Shares to Buy
portfolio_size = input("Enter the value of your portfolio:")
try:
    val = float(portfolio_size)
except ValueError:
    print("That's not a number! \n Try again:")
    portfolio_size = input("Enter the value of your portfolio:")

position_size = float(portfolio_size) / len(rv_dataframe.index)
for i in range(0, len(rv_dataframe['Ticker'])):
    rv_dataframe.loc[i, 'Number of Shares to Buy'] = math.floor(
        position_size / rv_dataframe['Price'][i])

print(rv_dataframe)

# export to excel
column_formats = {
    'A': ['Ticker', 'string'],
    'B': ['Price', 'dollar'],
    'C': ['Number of Shares to Buy', 'integer'],
    'D': ['Price-to-Earnings Ratio', 'float'],
    'E': ['PE Percentile', 'percent'],
    'F': ['Price-to-Book Ratio', 'float'],
    'G': ['PB Percentile', 'percent'],
    'H': ['Price-to-Sales Ratio', 'float'],
    'I': ['PS Percentile', 'percent'],
    'J': ['EV/EBITDA', 'float'],
    'K': ['EV/EBITDA Percentile', 'percent'],
    'L': ['EV/GP', 'float'],
    'M': ['EV/GP Percentile', 'percent'],
    'N': ['RV Score', 'percent']
}

write_to_excel(df=rv_dataframe,
               filepath='output\\value_strategy.xlsx',
               sheet_name='Value Strategy',
               column_formats=column_formats)
