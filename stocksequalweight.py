"""1: Equal_weight_S&P_500

Original from:
https://github.com/nickmccullum/algorithmic-trading-python/blob/master/finished_files/001_equal_weight_S%26P_500.ipynb

Python script that will accept the value of your portfolio and tell you how many shares of each S&P 500 
constituent you should purchase to get an equal-weight version of the index fund.

CSV with S&P stocks: (This is OLD)
http://nickmccullum.com/algorithmic-trading-python/sp_500_stocks.csv

Certificate SSL file:
C:\\Users\\i154424\\Documents\\Projects\\test\\stocksdata\\venv\\Lib\\site-packages\\certifi\\cacert.pem

20-12-2022
Arno Kemner
"""

import math  # The Python math module

import pandas as pd  # The Pandas data science library
import requests  # The requests library for HTTP requests in Python

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

my_columns = ['Ticker',
              'Price',
              'Market Capitalization',
              'Number Of Shares to Buy']


# Adding Stocks Data to a Pandas DataFrame
# Looping Through Tickers in chunk List of Stocks
final_dataframe = pd.DataFrame(columns=my_columns)
for symbol_string in symbol_strings:
    batch_api_call_url = f'https://sandbox.iexapis.com/stable/stock/market/batch/?types=quote&symbols={symbol_string}&token={IEX_CLOUD_API_TOKEN}'
    data = requests.get(batch_api_call_url).json()
    for symbol in symbol_string.split(','):
        new_data = pd.DataFrame([[symbol,
                                 data[symbol]['quote']['latestPrice'],
                                 data[symbol]['quote']['marketCap'],
                                 'N/A']],
                                columns=my_columns)
        final_dataframe = pd.concat([final_dataframe, new_data],
                                    ignore_index=True,
                                    axis=0)

# drop rows with None
final_dataframe = final_dataframe.dropna().reset_index()
# print(final_dataframe.loc[[135]])

# Calculating the Number of Shares to Buy
portfolio_size = input("Enter the value of your portfolio:")
try:
    val = float(portfolio_size)
except ValueError:
    print("That's not a number! \n Try again:")
    portfolio_size = input("Enter the value of your portfolio:")

position_size = float(portfolio_size) / len(final_dataframe.index)
for i in range(0, len(final_dataframe['Ticker'])):
    final_dataframe.loc[i, 'Number Of Shares to Buy'] = math.floor(
        position_size / final_dataframe['Price'][i])
print(final_dataframe)

# export to excel
column_formats = {
    'A': ['Ticker', 'string'],
    'B': ['Price', 'dollar'],
    'C': ['Market Capitalization', 'dollar'],
    'D': ['Number of Shares to Buy', 'integer']
}

write_to_excel(df=final_dataframe,
               filepath='output\\recommended_trades.xlsx',
               sheet_name='Recommended Trades',
               column_formats=column_formats)
