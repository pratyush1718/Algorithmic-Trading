# use stats (basic) end point and collect 50 and 200 day moving averages
import numpy as np
import pandas as pd
import requests
import math
from scipy.stats import percentileofscore as score
import xlsxwriter
from Secret import IEX_CLOUD_API_TOKEN, file_path
from statistics import mean
from Quantitative_Momentum_Strategy import hqm_forFinal
from Quantitative_Value_Strategy import rv_forFinal
from Financials_Based_Strategy import hfb_forFinal
from Analyst_Consensus_Strategy import acs_forFinal
from Sentiment_Analysis_Strategy import sas_forFinal
from ML_StockForecast import get30dayForecast


stocks = pd.read_csv(file_path)

#creating final dataFrame and appending data
my_columns = ['Ticker',
              'Current Price',
              'Number of Shares to Buy',
              'Final Algorithm Score',
              'Algorithms Recommendation',
              '30-Day Stock Forecast',
              'Recommended Target Price',
              'Recommended Stop Loss Price',
              'Past One Week News Trend',
              'HQM Score',
              'RV Score',
              'HFB Score',
              'ACS Score',
              'SAS Score']

final_df = pd.DataFrame(columns=my_columns)


for row in hqm_forFinal.index:
    final_df = final_df.append(

        pd.Series(

            [

                hqm_forFinal.loc[row, 'Ticker'],
                hqm_forFinal.loc[row, 'Price'],
                0,
                'N/A',
                'N/A',
                'N/A',
                'N/A',
                'N/A',
                'N/A',
                hqm_forFinal.loc[row, 'HQM Score'],
                rv_forFinal.loc[row, 'RV Score'],
                0,
                0,
                0.5


            ], index=my_columns

        ), ignore_index=True
    )

#appending HFB, ACS, and SAS Scores seperately since their DataFrames contain missing data

def appendOtherScores(scoreType, df):
    for row in df.index:
        for row2 in final_df.index:
            if(df.loc[row, 'Ticker'] == final_df.loc[row2, 'Ticker']):
                final_df.loc[row2, scoreType] = df.loc[row, scoreType]
                if(scoreType == 'SAS Score'):
                    final_df.loc[row2, 'Past One Week News Trend'] = df.loc[row, 'PastOneWeekNewsTrend']


appendOtherScores('HFB Score', hfb_forFinal)
appendOtherScores('ACS Score', acs_forFinal)
appendOtherScores('SAS Score', sas_forFinal)


def assignRating(AlgoScore):
    if AlgoScore >= 0.65:
        return 'Strong Buy'

    elif AlgoScore >= 0.55:
        return 'Buy'

    elif AlgoScore >= 0.4:
        return 'Overweight'

    elif AlgoScore >= 0.2:
        return 'Sell'

    return 'Strong Sell'

#dictionaries for operation storage

#metrics dict will help calculate final algorithm score
metrics = {
    'A': 'HQM Score',
    'B': 'RV Score',
    'C': 'HFB Score',
    'D': 'ACS Score',
    'E': 'SAS Score'
}

#reccomendations dict will help calculate Stop Loss Price, Target Price, and Number of Shares to Buy
Recommendations = {
    'Strong Buy': {'targetPricePadding': 1.22, 'stopLossPricePadding': 0.9, 'portfolioAllocation': 0.45},
    'Buy': {'targetPricePadding': 1.18, 'stopLossPricePadding': 0.95, 'portfolioAllocation': 0.35},
    'Overweight': {'targetPricePadding': 1.1, 'stopLossPricePadding': 0.98, 'portfolioAllocation': 0.2},
    'Sell': {'targetPricePadding': 1, 'stopLossPricePadding': 0.98, 'portfolioAllocation': 0},
    'Strong Sell': {'targetPricePadding': 0.9, 'stopLossPricePadding': 0.98, 'portfolioAllocation': 0}
}


#Performing Math Operations for Algorithm data and filling out Final DataFrame

for row in final_df.index:
    scoreValues = []
    for metric in metrics.keys():
        scoreValues.append(final_df.loc[row, metrics[metric]])
    final_df.loc[row, 'Final Algorithm Score'] = mean(scoreValues)
    final_df.loc[row, 'Algorithms Recommendation'] = assignRating(final_df.loc[row, 'Final Algorithm Score'])
    for row2 in acs_forFinal.index:
        if(acs_forFinal.loc[row2, 'Ticker'] == final_df.loc[row, 'Ticker']):
            if(final_df.loc[row,'Ticker'] == 'NVDA'): #check for NVDA stock since sanbox mode in IEX Cloud API provides inaccurate price target for NVDA
                final_df.loc[row, 'Recommended Target Price'] = 0.5 * acs_forFinal.loc[row2, 'Target Price']
            else:
                final_df.loc[row, 'Recommended Target Price'] = ((Recommendations[final_df.loc[row, 'Algorithms Recommendation']])['targetPricePadding']) * acs_forFinal.loc[row2, 'Target Price']
    final_df.loc[row, 'Recommended Stop Loss Price'] = ((Recommendations[final_df.loc[row, 'Algorithms Recommendation']])['stopLossPricePadding']) * final_df.loc[row, 'Current Price']

#print(final_df)


final_df.sort_values('Final Algorithm Score', ascending = False, inplace = True)
final_df.reset_index(drop=True, inplace = True)
final_df = final_df[final_df['Final Algorithm Score'] >= 0.5]
final_df = final_df[:50]
print(final_df)

#storing 30-day stock forecasts
for row in final_df.index:
    final_df.loc[row,'30-Day Stock Forecast'] = get30dayForecast(final_df.loc[row,'Ticker'])

#Storing portfolio size from input

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

StrongBuyCount = 0
BuyCount = 0
OverweightCount = 0

for row in final_df.index:
    signal = final_df.loc[row, 'Algorithms Recommendation']
    if signal == 'Strong Buy':
        StrongBuyCount+=1
    elif signal == 'Buy':
        BuyCount+=1
    else:
        OverweightCount+=1

#Calculates Number of Shares to Buy and allocates more money to stocks that have a high Algorithm Recommendation
for row in final_df.index:
    signal = final_df.loc[row, 'Algorithms Recommendation']
    moneyAllocated = Recommendations[signal]['portfolioAllocation']
    position_size = float(portfolio_size) * moneyAllocated
    if signal == 'Strong Buy':
        position_size = position_size/StrongBuyCount
    elif signal == 'Buy':
        position_size = position_size/BuyCount
    elif signal == 'Overweight':
        position_size = position_size/OverweightCount
    else:
        position_size = 0

    final_df.loc[row, 'Number of Shares to Buy'] = math.floor(position_size/final_df.loc[row, 'Current Price'])

#converting to excel output

writer = pd.ExcelWriter('Final Stock Recommendations.xlsx', engine='xlsxwriter')
final_df.to_excel(writer, sheet_name = 'Final Stock Recommendations', index=False)


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
    'B': ['Current Price', dollar_template],
    'C': ['Number of Shares to Buy', integer_template],
    'D': ['Final Algorithm Score', percent_template],
    'E': ['Algorithms Recommendation', string_template],
    'F': ['30-Day Stock Forecast', dollar_template],
    'G': ['Recommended Target Price', dollar_template],
    'H': ['Recommended Stop Loss Price', dollar_template],
    'I': ['Past One Week News Trend', string_template],
    'J': ['HQM Score', percent_template],
    'K': ['RV Score', percent_template],
    'L': ['HFB Score', percent_template],
    'M': ['ACS Score', percent_template],
    'N': ['SAS Score', percent_template]

}


for column in column_formats.keys():
    writer.sheets['Final Stock Recommendations'].set_column(f'{column}:{column}', 30, column_formats[column][1])
    writer.sheets['Final Stock Recommendations'].write(f'{column}1', column_formats[column][0], column_formats[column][1])

writer.save()