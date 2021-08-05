import numpy as np
import pandas as pd
import requests
import math
from scipy.stats import percentileofscore as score
import xlsxwriter
from test import IEX_CLOUD_API_TOKEN
from statistics import mean


stocks = pd.read_csv('C:/Users/Praty/OneDrive/Programming/Algorithmic-Trading/sp_500_stocks.csv')


#API Calls and Data Storage through Pandas DataFrames

symbol = 'AAPL'
api_url = f'https://sandbox.iexapis.com/stable/stock/{symbol}/quote?token={IEX_CLOUD_API_TOKEN}' #calls quote endpoint
data = requests.get(api_url).json()


price = data['latestPrice']
pe_ratio = data['peRatio']

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

symbol_groups = list(chunks(stocks['Ticker'], 100))
symbol_strings = []
for i in range(0, len(symbol_groups)):
    symbol_strings.append(','.join(symbol_groups[i]))

my_columns = ['Ticker', 'Price', 'Price-to-Earnings Ratio', 'Number of Shares to Buy']

final_dataframe = pd.DataFrame(columns=my_columns)

for symbol_string in symbol_strings:
    batch_api_call_url = f'https://sandbox.iexapis.com/stable/stock/market/batch/?types=quote&symbols={symbol_string}&token={IEX_CLOUD_API_TOKEN}'
    data = requests.get(batch_api_call_url).json()
    for symbol in symbol_string.split(','):
        final_dataframe = final_dataframe.append(
            pd.Series(
                [
                    symbol,
                    data[symbol]['quote']['latestPrice'],
                    data[symbol]['quote']['peRatio'],
                    'N/A'
                ], index = my_columns
            ), ignore_index=True
        )
#print(final_dataframe)

final_dataframe.sort_values('Price-to-Earnings Ratio', ascending=True, inplace=True)
final_dataframe = final_dataframe[final_dataframe['Price-to-Earnings Ratio'] > 0]
final_dataframe = final_dataframe[:50]
final_dataframe.reset_index(inplace=True, drop=True)
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
position_Size = float(portfolio_size)/len(final_dataframe)

for row in final_dataframe.index:
    final_dataframe.loc[row, 'Number of Shares to Buy'] = math.floor(position_Size/final_dataframe.loc[row, 'Price'])

print(final_dataframe)

symbol = 'AAPL'
batch_api_call_url2 = f'https://sandbox.iexapis.com/stable/stock/market/batch/?types=advanced-stats,quote&symbols={symbol}&token={IEX_CLOUD_API_TOKEN}'
data2 = requests.get(batch_api_call_url2).json()

#Building a better quantitative strategy model

#print(data2['AAPL']['advanced-stats'])  sample line for finding value metrics locations

# P/E Ratio
pe_ratio = data2[symbol]['quote']['peRatio']

# P/B Ratio
pb_ratio = data2[symbol]['advanced-stats']['priceToBook']

#P/S Ratio
ps_ratio = data2[symbol]['advanced-stats']['priceToSales']

#Enterprise Value divided by Earnings Before Interest, Taxes, Depreciation, and Amortization (EV/EBITDA)

enterprise_value = data2[symbol]['advanced-stats']['enterpriseValue']
ebitda = data2[symbol]['advanced-stats']['EBITDA']
ev_to_ebitda = enterprise_value/ebitda

# Enterprise Value divided by Gross Profit (EV/GP)
gross_profit = data2[symbol]['advanced-stats']['grossProfit']
ev_to_gross_profit = enterprise_value/gross_profit


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
    batch_api_call_url3 = f'https://sandbox.iexapis.com/stable/stock/market/batch?symbols={symbol_string}&types=quote,advanced-stats&token={IEX_CLOUD_API_TOKEN}'
    data3 = requests.get(batch_api_call_url3).json()
    for symbol in symbol_string.split(','):
        enterprise_value = data3[symbol]['advanced-stats']['enterpriseValue']
        ebitda = data3[symbol]['advanced-stats']['EBITDA']
        gross_profit = data3[symbol]['advanced-stats']['grossProfit']

        try:
            ev_to_ebitda = enterprise_value/ebitda
        except TypeError:
            ev_to_ebitda = np.NaN

        try:
            ev_to_gross_profit = enterprise_value/gross_profit
        except TypeError:
            ev_to_gross_profit = np.NaN

        rv_dataframe = rv_dataframe.append(
            pd.Series([
                symbol,
                data3[symbol]['quote']['latestPrice'],
                'N/A',
                data3[symbol]['quote']['peRatio'],
                'N/A',
                data3[symbol]['advanced-stats']['priceToBook'],
                'N/A',
                data3[symbol]['advanced-stats']['priceToSales'],
                'N/A',
                ev_to_ebitda,
                'N/A',
                ev_to_gross_profit,
                'N/A',
                'N/A'
            ],
                index = rv_columns),
            ignore_index = True
        )

#print(rv_dataframe['EV/EBITDA'])

##dealing with missing data

for column in ['Price-to-Earnings Ratio', 'Price-to-Book Ratio','Price-to-Sales Ratio',  'EV/EBITDA','EV/GP']:
    rv_dataframe[column].fillna(rv_dataframe[column].mean(), inplace = True) #replacing missing values with average values in that column

metrics = {
    'Price-to-Earnings Ratio': 'PE Percentile',
    'Price-to-Book Ratio': 'PB Percentile',
    'Price-to-Sales Ratio': 'PS Percentile',
    'EV/EBITDA': 'EV/EBITDA Percentile',
    'EV/GP': 'EV/GP Percentile'
}

for metric in metrics.keys():
    for row in rv_dataframe.index:
        rv_dataframe.loc[row, metrics[metric]] = score(rv_dataframe[metric], rv_dataframe.loc[row, metric])/100

#Calculating RV score

for row in rv_dataframe.index:
    value_percentiles = []
    for metric in metrics.keys():
        value_percentiles.append(rv_dataframe.loc[row, metrics[metric]])
    rv_dataframe.loc[row, 'RV Score'] = mean(value_percentiles)

rv_dataframe.sort_values('RV Score', ascending=True, inplace=True)
rv_dataframe = rv_dataframe[rv_dataframe['Price-to-Earnings Ratio'] > 0]
rv_dataframe = rv_dataframe[:50]
rv_dataframe.reset_index(drop=True, inplace = True)

portfolio_input()
position_size = float(portfolio_size)/len(rv_dataframe)

for row in rv_dataframe.index:
    rv_dataframe.loc[row, 'Number of Shares to Buy'] = math.floor(position_size/rv_dataframe.loc[row, 'Price'])

writer = pd.ExcelWriter('Quantitative Value Strategy.xlsx', engine='xlsxwriter')
rv_dataframe.to_excel(writer, sheet_name = 'Quantitative Value Strategy', index=False)


background_color = '#0a0a23'
font_color = '#ffffff'

string_template = writer.book.add_format(
    {
        'font_color': font_color,
        'bg_color': background_color,
        'border': 1
    }
)

dollar_template = writer.book.add_format(
    {
        'num_format':'$0.00',
        'font_color': font_color,
        'bg_color': background_color,
        'border': 1
    }
)

integer_template = writer.book.add_format(
    {
        'num_format':'0',
        'font_color': font_color,
        'bg_color': background_color,
        'border': 1
    }
)

float_template = writer.book.add_format(
    {
        'num_format':'0',
        'font_color': font_color,
        'bg_color': background_color,
        'border': 1
    }
)

percent_template = writer.book.add_format(
    {
        'num_format':'0.0%',
        'font_color': font_color,
        'bg_color': background_color,
        'border': 1
    }
)


column_formats = {
    'A': ['Ticker', string_template],
    'B': ['Price', dollar_template],
    'C': ['Number of Shares to Buy', integer_template],
    'D': ['Price-to-Earnings Ratio', float_template],
    'E': ['PE Percentile', percent_template],
    'F': ['Price-to-Book Ratio', float_template],
    'G': ['PB Percentile',percent_template],
    'H': ['Price-to-Sales Ratio', float_template],
    'I': ['PS Percentile', percent_template],
    'J': ['EV/EBITDA', float_template],
    'K': ['EV/EBITDA Percentile', percent_template],
    'L': ['EV/GP', float_template],
    'M': ['EV/GP Percentile', percent_template],
    'N': ['RV Score', percent_template]
}

for column in column_formats.keys():
    writer.sheets['Quantitative Value Strategy'].set_column(f'{column}:{column}', 25, column_formats[column][1])
    writer.sheets['Quantitative Value Strategy'].write(f'{column}1', column_formats[column][0], column_formats[column][1])

writer.save()
