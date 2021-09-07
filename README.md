
# Stock Recommendations using Algorithmic Trading

This project analyzes the stocks in the S&P500 Securities Fund and recommends the top 50 stocks
based on various evaluation metrics including Quantitative Momentum, Quantitative Value, Financials (balance sheet, income statement, and cash flow), Analyst Consensus, and Sentiment in news headlines. Final output is an excel spreadsheet with stock information and algorithm scores.

Key concepts used: Rest APIs, Data Analysis, Web Scraping (using BeautifulSoup), NLP, and Machine Learning with Stacked LSTM model.
## API References
#### IEX Cloud API
#### Get values for stock symbol from various endpoints

```http
  GET /stock/{symbol}/quote/
  GET /stock/{symbol}/stats/
  GET /stock/{symbol}/financials/
  GET /time-series/CORE_ESTIMATES/{symbol?}
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `{symbol}` | `string` | **Required**. Ticker of stock |


#### TIINGO API
#### Get close and open prices for stock symbol

```http
  GET daily/<ticker>/prices
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `<ticker>` | `string` | **Required**. Ticker of stock |




## Installation

- Install python 3 and pycharm from cmd

        $ sudo snap install pycharm-community --classic
        msiexec /i python<version>.msi

## Screenshots

- Sample Stock Forecast Chart
  ![Sample Stock Forecast Chart](https://sat02pap001files.storage.live.com/y4mBkr34kmpLQ6IHxZ78NX00ng8eKABHnSZLy_EzOPqPEa9CBtFOqAYMxfkSgHfYDlwCP3zfqVH6jVKOSqjNNDWyIMF-Xwv8A5YqoDUQZnST6jhAN3QVeU-CXL773isHQ_MNcG1LKHuu9YRxesyr4r4k46k-ztp1QEtmtd5uHOWQyqr9bT8hsm2FXQ60boKczvc?width=596&height=446&cropmode=none)
- Sample Excel Output Snip
  ![Sample Excel Output Snip](https://sat02pap001files.storage.live.com/y4mDUvpaJOE0BlSGjB4bD_lqQTiQnWccO35BuIGF9BF99y9B9CG4DabNX_NlbmHNFRPZEF4HF53zHTUtV8yvcBWpNdbAr2FURtNMTNGRkhRZcF-FM_kT4b74oOEDBxnq47NNeg2fP4GgRR6_oYaqIAByNsn2CBuMRODwNxmPHqDy3ak6Hd-uH-jHcYo0u54G0gc?width=1565&height=500&cropmode=none)

## Acknowledgements
- [Coursera](https://www.coursera.org/learn/data-analysis-with-python?specialization=ibm-data-science)
- [Freecodecamp](https://www.youtube.com/watch?v=xfzGZB4HhEE&list=LL&index=7&t=9611s)
- [finviz](https://finviz.com/)
- [stock forecasting](https://www.youtube.com/watch?v=H6du_pfuznE&list=WL&index=7)

## Authors

- [@pratyushchand](https://github.com/pratyush1718)

  