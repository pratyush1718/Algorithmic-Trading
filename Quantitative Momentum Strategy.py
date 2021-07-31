import numpy as np
import pandas as pd
import requests
import math
from scipy import stats
import xlsxwriter
from secret import IEX_CLOUD_API_TOKEN

stocks = pd.read_csv('C:\Python\sp_500_stocks.csv')


#API Calls and Data Storage through Pandas DataFrames

symbol = 'AAPL'
api_url = f'https://sandbox.iexapis.com/stable/stock/{symbol}/stats?token={IEX_CLOUD_API_TOKEN}' #called f string
data = requests.get(api_url).json()

print('yeah')

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

symbol_groups = list(chunks(stocks['Ticker'], 100))
symbol_strings = []
for i in range(0, len(symbol_groups)):
    symbol_strings.append(','.join(symbol_groups[i]))

my_columns = ['Ticker', 'Price', 'One-Year Price Return', 'Number of Shares to Buy']

final_dataframe = pd.DataFrame(columns=my_columns)

for symbol_string in symbol_strings:
    batch_api_call_url = f'https://sandbox.iexapis.com/stable/stock/market/batch/?types=price,stats,quote&symbols={symbol_string}&token={IEX_CLOUD_API_TOKEN}'
    data = requests.get(batch_api_call_url).json()
    for symbol in symbol_string.split(','):
        final_dataframe = final_dataframe.append(

            pd.Series(
                [
                    symbol,
                    data[symbol]['price'],
                    data[symbol]['stats']['year1ChangePercent'],
                    'N/A'

                ],
                index = my_columns
            ),
            ignore_index=True
        )
print(final_dataframe)

#Dropping low momentum stocks

final_dataframe.sort_values('One-Year Price Return', ascending=False, inplace=True) #inplace = true means this will modify the original dataframe instead of just returning a modified df
final_dataframe = final_dataframe[:50]
final_dataframe.reset_index(inplace=True)
print(final_dataframe)

def portfolio_input():
    global portfolio_size
    portfolio_size = input('Enter the total value of your portfolio: ')
    checker = False
    while(not checker):
        try:
            portfolio_size = float(portfolio_size)
            checker = True
        except:
            checker = False
            print('That is not a number!')
            portfolio_size = input('Quit playin and just enter the total value of your portfolio: ')


portfolio_input()

for i in range(0, len(final_dataframe)):
   final_dataframe.loc[i, 'Number of Shares to Buy'] = math.floor(portfolio_size/len(final_dataframe)/final_dataframe.loc[i, 'Price'])

print(final_dataframe)