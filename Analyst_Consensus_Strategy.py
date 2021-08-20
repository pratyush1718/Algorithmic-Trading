import numpy as np
import pandas as pd
import requests
import math
from scipy.stats import percentileofscore as score
import xlsxwriter
from Secret import IEX_CLOUD_API_TOKEN, file_path
from statistics import mean

stocks = pd.read_csv(file_path)
symbol= 'AAPL'

#API Calls and Data Storage through Pandas DataFrames
api_url = f'https://sandbox.iexapis.com/stable/time-series/CORE_ESTIMATES/{symbol}?token={IEX_CLOUD_API_TOKEN}'

data = requests.get(api_url).json()
print(data[0]['marketConsensus'])

#Building the Financials Based Strategy

my_columns = ['Ticker',
              'Price',
              'Number of Shares to Buy',
              'Market Consensus',
              'Market Consensus Percentile',
              'Target Price',
              'TP/CP Percentile',
              'ACS Score']

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

symbol_groups = list(chunks(stocks['Ticker'], 100))
symbol_strings = []
for i in range(0, len(symbol_groups)):
    symbol_strings.append(','.join(symbol_groups[i]))


acs_dataframe = pd.DataFrame(columns=my_columns)

for symbol_string in symbol_strings:
    batch_api_call_url = f'https://sandbox.iexapis.com/stable/stock/market/batch/?types=quote&symbols={symbol_string}&token={IEX_CLOUD_API_TOKEN}'
    data2 = requests.get(batch_api_call_url).json()
    for symbol in symbol_string.split(','):
        #Batch API calls were not permitted for the time-series/CORE_ESTIMATES endpoint, only availale for the quote endpoint
        #Therefore, two different api urls are utilized
        api_url = f'https://sandbox.iexapis.com/stable/time-series/CORE_ESTIMATES/{symbol}?token={IEX_CLOUD_API_TOKEN}'
        data = requests.get(api_url).json()
        if(data != []):
            acs_dataframe = acs_dataframe.append(
                pd.Series(
                    [
                        symbol,
                        data2[symbol]['quote']['latestPrice'],
                        'N/A',
                        data[0]['marketConsensus'],
                        'N/A',
                        data[0]['marketConsensusTargetPrice']/data2[symbol]['quote']['latestPrice'],
                        'N/A',
                        'N/A'

                    ], index=my_columns
                ), ignore_index = True
            )

#print(acs_dataframe)

metrics = {
    'Market Consensus': 'Market Consensus Percentile',
    'Target Price': 'TP/CP Percentile',
}

#Assigns percentile scores
for row in acs_dataframe.index:
    for metric in metrics.keys():
        acs_dataframe.loc[row, metrics[metric]] = score(acs_dataframe[metric], acs_dataframe.loc[row, metric])/100

#Calculates ACS score based on mean of percentile scores
for row in acs_dataframe.index:
    value_percentiles = []
    for metric in metrics.keys():
        value_percentiles.append(acs_dataframe.loc[row, metrics[metric]])
    acs_dataframe.loc[row, 'ACS Score'] = mean(value_percentiles)


#Function for converting numerical "market consensus" rating to a String-based consensus rating that is easier to understand
def convertingFromNumToConsensusString(numericalRating):
    stringRating = 'Neutral'
    if numericalRating > 0 and numericalRating < 50:
        stringRating = 'Overweight'
    elif numericalRating >= 50 and numericalRating < 100:
        stringRating = 'Buy'
    return stringRating

#Modifies the Target Price and Market conensus columns to enhance understanding and readability
for row in acs_dataframe.index:
    for metric in metrics.keys():
        if(metric== 'Target Price'):
            acs_dataframe.loc[row, metric] = acs_dataframe.loc[row, 'Price'] * acs_dataframe.loc[row, 'Target Price']
        else:
            acs_dataframe.loc[row, metric] = convertingFromNumToConsensusString(acs_dataframe.loc[row, metric])


acs_forFinal = acs_dataframe.copy()
acs_dataframe.sort_values('ACS Score', ascending = False, inplace = True)
acs_dataframe.reset_index(drop=True, inplace = True)
acs_dataframe = acs_dataframe[:50]
print(acs_dataframe)

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
position_size = float(portfolio_size)/len(acs_dataframe)

for row in acs_dataframe.index:
    acs_dataframe.loc[row, 'Number of Shares to Buy'] = math.floor(position_size/acs_dataframe.loc[row, 'Price'])

#Converting to excel output
writer = pd.ExcelWriter('Analyst Consensus Strategy.xlsx', engine='xlsxwriter')
acs_dataframe.to_excel(writer, sheet_name = 'Analyst Consensus Strategy', index=False)


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
        'num_format':'0.00',
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
    'D': ['Market Consensus', float_template],
    'E': ['Market Consensus Percentile', percent_template],
    'F': ['Target Price', float_template],
    'G': ['TP/CP Percentile', percent_template],
    'H': ['ACS Score', percent_template],
}

for column in column_formats.keys():
    writer.sheets['Analyst Consensus Strategy'].set_column(f'{column}:{column}', 30, column_formats[column][1])
    writer.sheets['Analyst Consensus Strategy'].write(f'{column}1', column_formats[column][0], column_formats[column][1])

writer.save()