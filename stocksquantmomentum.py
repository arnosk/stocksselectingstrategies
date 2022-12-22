"""2: Quantitative Momentum Strategy

Original from:
https://github.com/nickmccullum/algorithmic-trading-python/blob/master/finished_files/002_quantitative_momentum_strategy.ipynb

Python script investing strategy that selects the 50 stocks with the highest price momentum.
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

import pandas as pd  # The Pandas data science library
import requests  # The requests library for HTTP requests in Python
from scipy import stats  # The SciPy stats module

from config import IEX_CLOUD_API_TOKEN
from writerexcel import write_to_excel

# removed some unexisting tickers: DISCA, HFC, VIAC, WLTW
stocks = pd.read_csv('sp_500_stocks.csv')

# symbol = 'AAPL'
# api_url = f'https://sandbox.iexapis.com/stable/stock/{symbol}/stats?token={IEX_CLOUD_API_TOKEN}'
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
Real-world quantitative investment firms differentiate between "high quality" and "low quality" momentum stocks:

High-quality momentum stocks show "slow and steady" outperformance over long periods of time
Low-quality momentum stocks might not show any momentum for a long time, and then surge upwards.
The reason why high-quality momentum stocks are preferred is because low-quality momentum can often be cause by short-term news that is unlikely to be repeated in the future (such as an FDA approval for a biotechnology company).

To identify high-quality momentum, we're going to build a strategy that selects stocks from the highest percentiles of:

1-month price returns
3-month price returns
6-month price returns
1-year price returns
Let's start by building our DataFrame. You'll notice that I use the abbreviation hqm often. It stands for high-quality momentum
"""
hqm_columns = [
    'Ticker',
    'Price',
    'Number of Shares to Buy',
    'One-Year Price Return',
    'One-Year Return Percentile',
    'Six-Month Price Return',
    'Six-Month Return Percentile',
    'Three-Month Price Return',
    'Three-Month Return Percentile',
    'One-Month Price Return',
    'One-Month Return Percentile',
    'HQM Score'
]

hqm_dataframe = pd.DataFrame(columns=hqm_columns)

for symbol_string in symbol_strings:
    #     print(symbol_strings)
    batch_api_call_url = f'https://sandbox.iexapis.com/stable/stock/market/batch/?types=stats,quote&symbols={symbol_string}&token={IEX_CLOUD_API_TOKEN}'
    data = requests.get(batch_api_call_url).json()
    for symbol in symbol_string.split(','):
        new_data = pd.DataFrame([[symbol,
                                  data[symbol]['quote']['latestPrice'],
                                  'N/A',
                                  data[symbol]['stats']['year1ChangePercent'],
                                  'N/A',
                                  data[symbol]['stats']['month6ChangePercent'],
                                  'N/A',
                                  data[symbol]['stats']['month3ChangePercent'],
                                  'N/A',
                                  data[symbol]['stats']['month1ChangePercent'],
                                  'N/A',
                                  'N/A'
                                  ]],
                                columns=hqm_columns)
        hqm_dataframe = pd.concat([hqm_dataframe, new_data],
                                  ignore_index=True,
                                  axis=0)

# print(hqm_dataframe.columns)
print(hqm_dataframe)

# drop rows with None
# hqm_dataframe = hqm_dataframe.dropna().reset_index()
# hqm_dataframe = hqm_dataframe.mask(hqm_dataframe.eq('None')).dropna().reset_index()
for column in ['One-Year Price Return', 'Six-Month Price Return', 'Three-Month Price Return',  'One-Month Price Return']:
    hqm_dataframe[column].fillna(hqm_dataframe[column].mean(), inplace=True)


# Calculating Momentum Percentiles
time_periods = [
    'One-Year',
    'Six-Month',
    'Three-Month',
    'One-Month'
]

for row in hqm_dataframe.index:
    for time_period in time_periods:
        col_percentile = f'{time_period} Return Percentile'
        col_pricereturn = f'{time_period} Price Return'
        hqm_dataframe.loc[row, col_percentile] = stats.percentileofscore(
            hqm_dataframe[col_pricereturn],
            hqm_dataframe.loc[row, col_pricereturn]
        )/100

# Print each percentile score to make sure it was calculated properly
for time_period in time_periods:
    print(hqm_dataframe[f'{time_period} Return Percentile'])

# Print the entire DataFrame
# print(hqm_dataframe)

# Calculating the HQM Score
for row in hqm_dataframe.index:
    momentum_percentiles = []
    for time_period in time_periods:
        momentum_percentiles.append(
            hqm_dataframe.loc[row, f'{time_period} Return Percentile'])
    hqm_dataframe.loc[row, 'HQM Score'] = mean(momentum_percentiles)

# Selecting the 50 Best Momentum Stocks
hqm_dataframe = hqm_dataframe.sort_values(
    by='HQM Score', ascending=False, ignore_index=True)
hqm_dataframe = hqm_dataframe[:51]

# Calculating the Number of Shares to Buy
portfolio_size = input("Enter the value of your portfolio:")
try:
    val = float(portfolio_size)
except ValueError:
    print("That's not a number! \n Try again:")
    portfolio_size = input("Enter the value of your portfolio:")

position_size = float(portfolio_size) / len(hqm_dataframe.index)
for i in range(0, len(hqm_dataframe['Ticker'])):
    hqm_dataframe.loc[i, 'Number of Shares to Buy'] = math.floor(
        position_size / hqm_dataframe['Price'][i])
hqm_dataframe

print(hqm_dataframe)

# export to excel
column_formats = {
    'A': ['Ticker', 'string'],
    'B': ['Price', 'dollar'],
    'C': ['Number of Shares to Buy', 'integer'],
    'D': ['One-Year Price Return', 'percent'],
    'E': ['One-Year Return Percentile', 'percent'],
    'F': ['Six-Month Price Return', 'percent'],
    'G': ['Six-Month Return Percentile', 'percent'],
    'H': ['Three-Month Price Return', 'percent'],
    'I': ['Three-Month Return Percentile', 'percent'],
    'J': ['One-Month Price Return', 'percent'],
    'K': ['One-Month Return Percentile', 'percent'],
    'L': ['HQM Score', 'integer']
}

write_to_excel(df=hqm_dataframe,
               filepath='output\\momentum_strategy.xlsx',
               sheet_name='Momentum Strategy',
               column_formats=column_formats)
