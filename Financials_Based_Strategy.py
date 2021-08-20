import numpy as np
import pandas as pd
import requests
import math
from scipy.stats import percentileofscore as score
import xlsxwriter
from Secret import IEX_CLOUD_API_TOKEN, file_path
from statistics import mean

stocks = pd.read_csv(file_path)

#API Calls and Data Storage through Pandas DataFrames
symbol= 'AAPL'
api_url = f'https://sandbox.iexapis.com/stable/stock/{symbol}/financials?token={IEX_CLOUD_API_TOKEN}'

data = requests.get(api_url).json()

print(data['financials'][0])

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

symbol_groups = list(chunks(stocks['Ticker'], 100))
symbol_strings = []
for i in range(0, len(symbol_groups)):
    symbol_strings.append(','.join(symbol_groups[i]))

my_columns = ['Ticker', 'Price', 'Total Assets', 'Number of Shares to Buy']

final_dataframe = pd.DataFrame(columns=my_columns)

for symbol_string in symbol_strings:
    batch_api_call_url = f'https://sandbox.iexapis.com/stable/stock/market/batch/?types=quote,financials&symbols={symbol_string}&token={IEX_CLOUD_API_TOKEN}'
    data = requests.get(batch_api_call_url).json()
    for symbol in symbol_string.split(','):
        if(data[symbol]['financials']):
            #if(data[symbol]['financials']['financials'][0]['totalCash'] - data[symbol]['financials']['financials'][0]['cashFlowFinancing'] < 0):
              #  print(data[symbol])
            final_dataframe = final_dataframe.append(
                pd.Series(
                    [
                        symbol,
                        data[symbol]['quote']['latestPrice'],
                        data[symbol]['financials']['financials'][0]['totalAssets'],
                        'N/A'
                    ], index = my_columns
                ), ignore_index=True
            )
final_dataframe.sort_values('Total Assets', ascending=False, inplace=True)
final_dataframe = final_dataframe[:50]
final_dataframe.reset_index(inplace=True, drop=True)
#print(final_dataframe)

#Building a better Financials Based Strategy that utilizes multiple evaluation metrics

hfb_columns = [
    'Ticker',
    'Price',
    'Number of Shares to Buy',
    'Total Assets/Total Liabilities',
    'TA/TL Percentile',
    'Current Assets/Current Liabilities',
    'CA/CL Percentile',
    'Operating Income/Total Revenue',
    'OI/TR Percentile',
    'Total Cash+Cash Flow Financing',
    'TC+CFF Percentile',
    'HFB Score'
]
hfb_dataframe = pd.DataFrame(columns=hfb_columns)

for symbol_string in symbol_strings:
    batch_api_call_url2 = f'https://sandbox.iexapis.com/stable/stock/market/batch/?types=quote,financials&symbols={symbol_string}&token={IEX_CLOUD_API_TOKEN}'
    data2 = requests.get(batch_api_call_url2).json()
    for symbol in symbol_string.split(','):
        if(data2[symbol]['financials']): ##conditional scatters over missing data
            total_assets = data2[symbol]['financials']['financials'][0]['totalAssets']
            total_liabilities = data2[symbol]['financials']['financials'][0]['totalLiabilities']
            current_assets = data2[symbol]['financials']['financials'][0]['currentAssets']
            current_liabilities = data2[symbol]['financials']['financials'][0]['otherCurrentLiabilities']
            operating_income = data2[symbol]['financials']['financials'][0]['operatingIncome']
            total_revenue = data2[symbol]['financials']['financials'][0]['totalRevenue']
            total_cash = data2[symbol]['financials']['financials'][0]['totalRevenue']
            cash_flow_financing = data2[symbol]['financials']['financials'][0]['totalRevenue']

            hfb_dataframe = hfb_dataframe.append(
                pd.Series([
                    symbol,
                    data2[symbol]['quote']['latestPrice'],
                    'N/A',
                    total_assets/total_liabilities,
                    'N/A',
                    current_assets/current_liabilities,
                    'N/A',
                    operating_income/total_revenue,
                    'N/A',
                    total_cash+cash_flow_financing,
                    'N/A',
                    'N/A'
                ],
                    index = hfb_columns),
                ignore_index = True
            )

#print(hfb_dataframe['Total Assets/Total Liabilities'])

metrics = {
    'Total Assets/Total Liabilities': 'TA/TL Percentile',
    'Current Assets/Current Liabilities': 'CA/CL Percentile',
    'Operating Income/Total Revenue': 'OI/TR Percentile',
    'Total Cash+Cash Flow Financing': 'TC+CFF Percentile',
}

#Assigns percentile scores
for metric in metrics.keys():
    for row in hfb_dataframe.index:
        hfb_dataframe.loc[row, metrics[metric]] = score(hfb_dataframe[metric], hfb_dataframe.loc[row, metric])/100

#Calculates HFB score based on mean of percentile scores
for row in hfb_dataframe.index:
    value_percentiles = []
    for metric in metrics.keys():
        value_percentiles.append(hfb_dataframe.loc[row, metrics[metric]])
    hfb_dataframe.loc[row, 'HFB Score'] = mean(value_percentiles)



hfb_dataframe = hfb_dataframe[hfb_dataframe['Total Assets/Total Liabilities'] > 1]
hfb_dataframe = hfb_dataframe[hfb_dataframe['Total Cash+Cash Flow Financing'] > 0]
hfb_forFinal = hfb_dataframe.copy()
hfb_dataframe.sort_values('HFB Score', ascending = False, inplace = True)
hfb_dataframe.reset_index(drop=True, inplace = True)
hfb_dataframe = hfb_dataframe[:50]
print(hfb_dataframe)

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
position_size = float(portfolio_size)/len(hfb_dataframe)

for row in hfb_dataframe.index:
    hfb_dataframe.loc[row, 'Number of Shares to Buy'] = math.floor(position_size/hfb_dataframe.loc[row, 'Price'])

#Converting to excel output

writer = pd.ExcelWriter('Financials Based Strategy.xlsx', engine='xlsxwriter')
hfb_dataframe.to_excel(writer, sheet_name = 'Financials Based Strategy', index=False)


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
        'num_format':'0.000',
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
    'D': ['Total Assets/Total Liabilities', float_template],
    'E': ['TA/TL Percentile', percent_template],
    'F': ['Current Assets/Current Liabilities', float_template],
    'G': ['CA/CL Percentile', percent_template],
    'H': ['Operating Income/Total Revenue', float_template],
    'I': ['OI/TR Percentile', percent_template],
    'J': ['Total Cash+Cash Flow Financing', float_template],
    'K': ['TC+CFF Percentile', percent_template],
    'L': ['HFB Score', percent_template],
}

for column in column_formats.keys():
    writer.sheets['Financials Based Strategy'].set_column(f'{column}:{column}', 30, column_formats[column][1])
    writer.sheets['Financials Based Strategy'].write(f'{column}1', column_formats[column][0], column_formats[column][1])

writer.save()