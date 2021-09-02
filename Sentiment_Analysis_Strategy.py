from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import urllib
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import pandas as pd
import numpy as np
import requests
import math
from scipy.stats import percentileofscore as score
import xlsxwriter
from Secret import IEX_CLOUD_API_TOKEN, file_path
from statistics import mean
from datetime import date, timedelta, datetime

stocks = pd.read_csv(file_path)
monthNames = {'Jan': '01',
              'Feb': '02',
              'Mar': '03',
              'Apr': '04',
              'May': '05',
              'Jun': '06',
              'Jul': '07',
              'Aug': '08',
              'Sep': '09',
              'Oct': '10',
              'Nov': '11',
              'Dec': '12'}

lastWeekDate = date.today() - timedelta(days=8)
lastWeekDate = lastWeekDate.strftime(format = '%m-%e-%y')

allNews = {}
news_tables = {}

def convertDate(newsDate):
    num = monthNames[newsDate[:3]]
    newDate = num + newsDate[3:]
    return newDate

#parsing through table-row tags on the finviz site and scraping article data for every stock for the past week
for ticker in stocks['Ticker']:
    parsedData = []
    finviz_url = 'https://finviz.com/quote.ashx?t='
    url = finviz_url + ticker
    try:
        req = Request(url=url,headers={'user-agent': 'my-app2'})
        response = urlopen(req)
        html = BeautifulSoup(response, 'html')
        news_table = html.find(id='news-table') #returns elements with id = news-table
        news_tables[ticker] = news_table
        for row in news_table.findAll('tr'):
            title = row.a.text #returns title of news article. .a. is done to get anchor tag
            date_data = row.td.text.split(' ') #returns date of news article

            if len(date_data) == 1:
                time = date_data[0]
            else:
                date = date_data[0]
                time = date_data[1]


            if convertDate(date)[3:5] <= lastWeekDate[3:5] and convertDate(date)[0:2] <= lastWeekDate[0:2]:
                break

            parsedData.append(title)
        allNews[ticker] = parsedData
    except urllib.error.HTTPError:
        print(ticker + ' not found') #for stocks not found on finviz


my_columns = ['Ticker', 'Mean Sentimental Score', 'SAS Score', 'PastOneWeekNewsTrend']
sas_dataframe = pd.DataFrame(columns=my_columns)

#Running sentiment analysis on the titles of articles for every stock, calculating a mean compound score, and appending it to the dataframe
for ticker, listNews in allNews.items():
    vader = SentimentIntensityAnalyzer()
    newsListCompoundScores = []
    for newsArticle in listNews:
        #print(vader.polarity_scores(newsArticle))
        newsListCompoundScores.append(vader.polarity_scores(newsArticle)['compound'])

    if(newsListCompoundScores != []):
        sas_dataframe = sas_dataframe.append(
            pd.Series(
                [
                    ticker,
                    mean(newsListCompoundScores),
                    'N/A',
                    'N/A'

                ], index=my_columns
            ), ignore_index=True
        )


def trendReturn(compoundScore):
    if compoundScore >= 0.5:
        return 'Very Positive'
    elif compoundScore > 0.1:
        return 'Positive'
    elif compoundScore <= -0.5:
        return 'Very Negative'
    elif compoundScore < -0.1:
        return 'Negative'

    return 'Neutral'

#Calculating SAS score and assigning a news trend value
for row in sas_dataframe.index:
    sas_dataframe.loc[row,'SAS Score'] = score(sas_dataframe['Mean Sentimental Score'], sas_dataframe.loc[row,'Mean Sentimental Score'])/100
    sas_dataframe.loc[row,'PastOneWeekNewsTrend'] = trendReturn(sas_dataframe.loc[row,'Mean Sentimental Score'])


sas_dataframe.sort_values('SAS Score',ascending=False,inplace=True)
sas_dataframe.reset_index(drop=True, inplace=True)
sas_forFinal = sas_dataframe.copy()
sas_dataframe = sas_dataframe[:50]
print(sas_dataframe)

#converting to excel output
writer = pd.ExcelWriter('Sentiment Analysis Strategy.xlsx', engine='xlsxwriter')
sas_dataframe.to_excel(writer, sheet_name = 'Sentiment Analysis Strategy', index=False)


background_color = '#0a0a23'
font_color = '#ffffff'

string_template = writer.book.add_format(
    {
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
    'B': ['Mean Sentimental Score', float_template],
    'C': ['SAS Score', percent_template],
    'D': ['PastOneWeekNewsTrend', string_template],

}


for column in column_formats.keys():
    writer.sheets['Sentiment Analysis Strategy'].set_column(f'{column}:{column}', 25, column_formats[column][1])
    writer.sheets['Sentiment Analysis Strategy'].write(f'{column}1', column_formats[column][0], column_formats[column][1])

writer.save()