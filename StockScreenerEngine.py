#Author: Brendan MacIntyre
#Date: 9/20/2021
#Description: This program serves as back end stock screener engine. It pulls stock info 
#              from the TD Ameritrade APIs and allows a user to filter and sort the data.

from get_all_tickers import get_tickers as gt
import API_urls
import requests
import pandas as pd
import PySimpleGUI as sg

def authenticate_API_key(key):
    """
    Creates a test response using API key, and checks that API key is functional. 

    Args:
        key: User's API key
    
    Returns:
        True if API key works, and False if API key is invalid.
    """
    #Get test request
    test_params = {'apikey': key, 'symbol': 'AAPL'}
    test_result = requests.get(API_urls.quotes_url, params = test_params)
   
    #Test request returned an invalid response
    if "invalid" in test_result.text.lower():
        return False
    else:
        return True


class StockScreenerEngine:
    """
    This class represents a stock screener object.
    Main methods to use are as follows:

    query: Query stock data based on inputted atributes
    sort_query_results: Sorts query results based on attribute given
    get_query_results: Returns the query results dataframe
    """

    def __init__(self, API_key, instruments_url=API_urls.instruments_url, 
                 quotes_url=API_urls.quotes_url, progress_bar = True):
        """
        Initializes StockScreenerEngine with dataframe of stock data from all stocks in NASDAQ, NYSE, and AMEX.

        Args:
            API_key: A string containing the key to access the TD Ameritrade APIs
            instruments_url: API resource url to get instrument/fundamental data, default set to current url (9/9/2021)
            quotes_url: API resource url to get quote data, default set to current url (9/19/2021)
            progress_bar: Set to True if user wants progress bar to be displayed during init, default set to True
        """
        #Initialize API
        self._key = API_key
        self._instruments_url = instruments_url
        self._quotes_url = quotes_url
        self._cancelled = False
        
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
            #Display progress bar
            if progress_bar:
                if not sg.one_line_progress_meter('Stock Screener', len(self._quotes_data), len(self._all_tickers),
                                                   'Loading stock data, please wait...', orientation='h'):
                    self._cancelled = True
                    break
            
            #API params and results
            tickers = self._all_tickers[start:end]
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
                #Add description and exchange attributes
                fundamental_data['description'] = instrument_results[ticker]['description']
                fundamental_data['exchange'] = instrument_results[ticker]['exchange']
                self._fundamental_data.append(fundamental_data)
            for ticker in quote_results:
                self._quotes_data.append(quote_results[ticker])
            
            #Next set of tickers
            start = end
            end += 500

        #Create dataframe of all data 
        quotes_data_params = ['symbol','regularMarketLastPrice','lastPrice','regularMarketPercentChangeInDouble','totalVolume']
        fundamental_df = pd.DataFrame(self._fundamental_data).sort_values(by = ['symbol'], ignore_index=True)
        quotes_df = pd.DataFrame(self._quotes_data, columns = quotes_data_params).sort_values(by = ['symbol'],ignore_index=True).drop('symbol',1)
        self._all_stock_data = pd.concat([fundamental_df,quotes_df],axis=1)
        new_column_names = {"symbol": "Symbol", "description": "Description", "exchange": "Exchange", "marketCap": "Market Cap (Millions)",
                            "regularMarketLastPrice": "Price", "regularMarketPercentChangeInDouble": "Percent Change",
                            "peRatio": "P/E", "totalVolume": "Volume"}
        self._all_stock_data.rename(columns = new_column_names, inplace=True)
        
        #Set default query results
        self._query_results = self._all_stock_data.copy()

        #Close progress bar
        if progress_bar:
            sg.one_line_progress_meter_cancel()
    

    def init_cancelled(self):
        """
        Returns True if the progress bar window was cancelled mid initialization.
        """
        return self._cancelled
        

    def get_all_stock_data(self):
        """
        Returns dataframe of all stock data unfiltered.
        """
        return self._all_stock_data
    

    def get_query_results(self, columns_list = ['Symbol','Description','Exchange','Market Cap (Millions)','Price','Percent Change','P/E','Volume']):
        """
        Returns dataframe of query results with specified attributes to display. 

        Args:
            columns_list: Attributes to display in dataframe, default set to display symbol, description,
            market cap, %change, P/E, and volume
        """
        return self._query_results[columns_list]


    def reset_query(self):
        """"
        Resets query results.
        """
        self._query_results = self.get_all_stock_data().copy()


    def available_filters(self):
        """
        Returns the currently available query filters for GUI.
        """
        filters = ['Symbol','Description','Exchange','Market Cap (Millions)','Price','Percent Change','P/E','Volume']
        return filters


    def query(self, **kwargs):
        """
        Queries stock data based on arguments given. 
        Ex). self.query(Exchange = 'NASDAQ', Volume = [0,20000])

        Keyword Args:
            Attributes to filter by
            Numerical filters must be entered as a list: attribute = [min_value, max_value]  
            Nonnumerical filters must be entered as a string: attribute = 'filter'
        """
        for arg in kwargs:
            filter_by = arg
            filter = kwargs.get(arg)
            if type(filter) == str:
                #String filter
                self._query_results = self._query_results[self._query_results[filter_by].str.contains(filter, case = False)]
            if type(filter) == list:
                #Numerical filter
                min = filter[0]
                max = filter[1]
                self._query_results = self._query_results[(self._query_results[filter_by] >= min) & (self._query_results[filter_by] <= max)]
        
        self._query_results.reset_index(drop = True)


    def sort_query_results(self, atribute, is_ascending = True):
        """
        Sorts query results based on attribute given. Sorts in ascending or descending order.

        Args:
            atribute: String of column name to sort by.
            is_ascending: True (default) if ascending order and False if descending order is desired
        """
        self._query_results = self._query_results.sort_values(by = [atribute], ascending=is_ascending, ignore_index=True)