from get_all_tickers import get_tickers as gt
import API_keys
import API_urls
import requests
import pandas as pd
import time

class StockScreenerEngine:
    """
    This class represents a stock screener object.
    """

    def __init__(self, API_key, instruments_url, quotes_url):
        """
        Initializes StockScreenerEngine with stock data from all stocks in NASDAQ, NYSE, and NASDAQ.

        """
        #Initialize API
        self._key = API_key
        self._instruments_url = instruments_url
        self._quotes_url = quotes_url
        
        #Get all unique tickers on NYSE, NASDAQ, AMEX 
        self._all_tickers = list(set(gt.get_tickers()))
        #Format tickers
        for index in range(len(self._all_tickers)):
            self._all_tickers[index] = self._all_tickers[index].replace("/",".")
            self._all_tickers[index] = self._all_tickers[index].strip()

        start = 0
        end = 500
        self._fundamental_data = []
        self._quotes_data = []
        #Get stock fundamental data and price quotes
        while start < len(self._all_tickers):
            tickers = self._all_tickers[start:end]
            
            #API params and results
            API_instruments_params = {'apikey': self._key, 'symbol': tickers, 'projection': 'fundamental'}
            API_quotes_params = {'apikey': self._key, 'symbol': ",".join(tickers)}
            instrument_results = requests.get(self._instruments_url, params=API_instruments_params).json()
            quote_results = requests.get(self._quotes_url, params = API_quotes_params).json()

            #Retry quotes request if not all data returned (API method currently broken, sometimes returns incomplete request)
            while len(quote_results) != len(instrument_results):
                quote_results = requests.get(self._quotes_url, params = API_quotes_params).json()

            #Unpack data
            for ticker in instrument_results:
                fundamental_data = instrument_results[ticker]['fundamental']
                fundamental_data['description'] = instrument_results[ticker]['description']
                fundamental_data['exchange'] = instrument_results[ticker]['exchange']
                self._fundamental_data.append(fundamental_data)
            for ticker in quote_results:
                self._quotes_data.append(quote_results[ticker])
            
            start = end
            end += 500

        #Create dataframe of all data 
        quotes_data_params = ['symbol','regularMarketLastPrice','lastPrice','totalVolume']
        fundamental_df = pd.DataFrame(self._fundamental_data).sort_values(by = ['symbol'], ignore_index=True)
        quotes_df = pd.DataFrame(self._quotes_data, columns = quotes_data_params).sort_values(by = ['symbol'],ignore_index=True).drop('symbol',1)
        self._all_stock_data = pd.concat([fundamental_df,quotes_df],axis=1)
        self._query_results = self._all_stock_data.copy()

    def get_all_stock_data(self):
        """
        Returns dataframe of all stock data unfiltered
        """
        return self._all_stock_data
    
    def get_query_results(self):
        "Returns query results"
        return self._query_results

    def reset_query(self):
        "Resets query results"
        self._query_results = self.get_all_stock_data().copy()

    def query(self, **kwargs):
        """
        """
        for arg in kwargs:
            filter_by = arg
            filter = kwargs.get(arg)
            if type(filter) == str:
                self._query_results = self._query_results[self._query_results[filter_by] == filter]
            if type(filter) == list:
                min = filter[0]
                max = filter[1]
                self._query_results = self._query_results[(self._query_results[filter_by] >= min) & (self._query_results[filter_by] <= max)]
        
        self._query_results.reset_index(drop = True)

    def sort_query_results(self, atribute, is_ascending = True):
        """
        """
        self._query_results = self._query_results.sort_values(by = [atribute], ascending=is_ascending, ignore_index=True)

screener = StockScreenerEngine(API_keys.ameritrade_API_key, API_urls.instruments_url, API_urls.quotes_url)
screener.query(exchange = 'NYSE', totalVolume = [0,4000])
screener.sort_query_results('totalVolume')
print(screener.get_query_results())


