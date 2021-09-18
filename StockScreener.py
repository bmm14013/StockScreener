from get_all_tickers import get_tickers as gt
import API_keys
import API_urls
import requests
import pandas as pd
import time

class StockScreener:
    """
    """

    def __init__(self, API_key):
        """
        """
        #Initialize API
        self._key = API_key
        self._instruments_url = API_urls.instruments_url
        self._quotes_url = API_urls.quotes_url
        
        #Get all tickers on NYSE, NASDAQ, AMEX 
        self._all_tickers = gt.get_tickers()
        #Format tickers
        for index in range(len(self._all_tickers)):
            self._all_tickers[index] = self._all_tickers[index].replace("/",".")
            self._all_tickers[index] = self._all_tickers[index].strip()


        start = 0
        end = 500
        self._fundamental_data = []
        self._quotes_data = []
        while start < len(self._all_tickers):
            tickers = self._all_tickers[start:end]
           # print(tickers)
            API_instruments_params = {'apikey': self._key, 'symbol': tickers, 'projection': 'fundamental'}
            API_quotes_params = {'apikey': self._key, 'symbol': ",".join(tickers)}

            instrument_data = requests.get(self._instruments_url, params=API_instruments_params).json()
            quote_data = requests.get(self._quotes_url, params = API_quotes_params).json()
            print(len(instrument_data))
            print(len(quote_data))
            while len(quote_data) != len(instrument_data):
                quote_data = requests.get(self._quotes_url, params = API_quotes_params).json()
                print(len(quote_data))
                time.sleep(.25)
            start = end
            end += 500
            for ticker in instrument_data:
                self._fundamental_data.append(instrument_data[ticker]['fundamental'])
            for ticker in quote_data:
                self._quotes_data.append(quote_data[ticker])
            print(len(self._fundamental_data))
            print(len(self._quotes_data))

        print(len(self._fundamental_data))
        print(len(self._quotes_data))

        quotes_df = pd.DataFrame(self._quotes_data)
        fundamentals_df = pd.DataFrame(self._fundamental_data)

        data_df = pd.concat([fundamentals_df, quotes_df], axis=1)

        print(data_df)

    def query(self, **kwargs):
        """
        """
        for arg in kwargs:
            filter = {arg: kwargs.get(arg)}




screener = StockScreener(API_keys.ameritrade_API_key)


