import numpy as np
import pandas as pd
import requests
import xlsxwriter
import math
from Secret import IEX_CLOUD_API_TOKEN

stocks = pd.read_csv('C:\Python\sp_500_stocks.csv')
print(stocks)

#API Calls and Data Storage through Pandas DataFrames

symbol = 'AAPL'
api_url = f'https://sandbox.iexapis.com/stable/stock/{symbol}/quote/?token={IEX_CLOUD_API_TOKEN}' #called f string
data = requests.get(api_url).json()
print(data)
price = data['latestPrice']
market_cap = data['marketCap']

my_columns = ['Ticker', 'Stock Price', 'Market Capitalization', '# shares to buy']
final_dataframe = pd.DataFrame(columns = my_columns)
final_dataframe.append(
    pd.Series(
        [symbol,
         price,
         market_cap,
         'N/A'
         ],
    index = my_columns
    ),
    ignore_index = True
)

final_dataframe = pd.DataFrame(columns = my_columns)
for stock in stocks['Ticker'][:5]:
    api_url = f'https://sandbox.iexapis.com/stable/stock/{symbol}/quote/?token={IEX_CLOUD_API_TOKEN}' #called f string
    data = requests.get(api_url).json()
    final_dataframe = final_dataframe.append(
        pd.Series(
            [stock,
             data['latestPrice'],
             data['marketCap'],
             'N/A'
             ],
            index = my_columns
        ),
        ignore_index = True
    )

print(final_dataframe)

#Creating chunks of stocks for Batch API calls

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

symbol_groups = list(chunks(stocks['Ticker'], 100))
symbol_strings = []
for i in range(0, len(symbol_groups)):
    symbol_strings.append(','.join(symbol_groups[i]))

final_dataframe = pd.DataFrame(columns=my_columns)
for symbol_string in symbol_strings:
    batch_api_call_url = f'https://sandbox.iexapis.com/stable/stock/market/batch?symbols={symbol_string}&types=quote&token={IEX_CLOUD_API_TOKEN}'
    data = requests.get(batch_api_call_url).json()
    for symbol in symbol_string.split(','):
        final_dataframe = final_dataframe.append(

           pd.Series(
               [
                   symbol,
                   data[symbol]['quote']['latestPrice'],
                   data[symbol]['quote']['marketCap'],
                   'N/A'

               ],
               index = my_columns
           ),
        ignore_index=True

        )

#print(final_dataframe)

#Inputting account value and printing #shares to buy for equal weight distribution in the S&P 500

portfolio_size = input('Enter the value of your portfolio: ')
CheckerBool = False
while(not CheckerBool):
    try:
        portfolio_size = float(portfolio_size)
        CheckerBool = True
    except ValueError:
        CheckerBool = False
        print('That is not a number!')
        portfolio_size = input('Quit playin and just enter the value of your portfolio: ')

position_size = portfolio_size/len(final_dataframe.index)
print(position_size)

for i in range(0, len(final_dataframe.index)):
    final_dataframe.loc[i, '# shares to buy'] = math.floor(position_size/final_dataframe.loc[i, 'Stock Price'])
print(final_dataframe)

#converting pandas dataframe into excel sheet

writer = pd.ExcelWriter('Recommended Trades.xlsx', engine = 'xlsxwriter')
final_dataframe.to_excel(writer, 'Recommended Trades', index = False)

background_color = '#0a0a23'
font_color = '#ffffff'

string_format = writer.book.add_format(
    {
        'font_color': font_color,
        'bg_color': background_color,
        'border': 1
    }
)
dollar_format = writer.book.add_format(
    {
        'num_format': '$0.00',
        'font_color': font_color,
        'bg_color': background_color,
        'border': 1
    }
)
integer_format = writer.book.add_format(
    {
        'num_format': '0',
        'font_color': font_color,
        'bg_color': background_color,
        'border': 1
    }
)

# writer.sheets['Recommended Trades'].write('A1', 'Ticker', string_format)
# writer.sheets['Recommended Trades'].write('B1', 'Stock Price', string_format)
# writer.sheets['Recommended Trades'].write('C1', 'Market Capitalization', string_format)
# writer.sheets['Recommended Trades'].write('D1', '# shares to buy', string_format)

column_format = {
    'A': ['Ticker', string_format],
    'B': ['Stock Price', dollar_format],
    'C': ['Market Capitalization', dollar_format],
    'D': ['# shares to buy', integer_format]
}

for column in column_format.keys():
    writer.sheets['Recommended Trades'].set_column(f'{column}:{column}', 18, column_format[column][1]) #for elements
    writer.sheets['Recommended Trades'].write(f'{column}1', column_format[column][0], column_format[column][1]) #for header
writer.save()

