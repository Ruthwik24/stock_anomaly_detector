import yfinance as yf
import pandas as pd
from datetime import datetime
import time

class DataFetcher:
    def __init__(self):
        self.last_fetch_time = {}

    def fetch_stock_data(self, ticker, period='1d', interval='5m'):
        """
        Fetch stock data from Yahoo Finance API with rate limiting
        """
        # Implement basic rate limiting
        if ticker in self.last_fetch_time:
            elapsed = time.time() - self.last_fetch_time[ticker]
            if elapsed < 2:  # 2 seconds between requests
                time.sleep(2 - elapsed)
        
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period=period, interval=interval)
            self.last_fetch_time[ticker] = time.time()
            return data[['Close']].dropna()
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return None

    def validate_data(self, data, ticker):
        """
        Validate the fetched data
        """
        if data is None or data.empty:
            print(f"No data returned for {ticker}")
            return False
        
        if 'Close' not in data.columns:
            print(f"Missing 'Close' column in data for {ticker}")
            return False
            
        return True