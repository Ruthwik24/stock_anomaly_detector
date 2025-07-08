import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import time
import smtplib
from email.mime.text import MIMEText
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

class StockMonitor:
    def __init__(self, tickers, threshold=3.0, window_size=20):
        """
        Initialize the stock monitor with tickers to watch, anomaly threshold, and moving window size.
        
        Args:
            tickers (list): List of stock tickers to monitor (e.g., ['AAPL', 'MSFT'])
            threshold (float): Z-score threshold for anomaly detection
            window_size (int): Number of data points to consider for moving statistics
        """
        self.tickers = tickers
        self.threshold = threshold
        self.window_size = window_size
        self.history = {ticker: pd.DataFrame(columns=['Close', 'Mean', 'Std', 'Z-Score']) 
                        for ticker in tickers}
        
    def fetch_data(self, ticker, period='1d', interval='5m'):
        """
        Fetch recent stock data from Yahoo Finance API.
        
        Args:
            ticker (str): Stock ticker symbol
            period (str): Time period to fetch (1d, 5d, 1mo, etc.)
            interval (str): Data interval (1m, 5m, 15m, 1h, 1d, etc.)
            
        Returns:
            pd.DataFrame: DataFrame with stock data
        """
        stock = yf.Ticker(ticker)
        data = stock.history(period=period, interval=interval)
        return data[['Close']].dropna()
    
    def detect_anomalies(self, ticker):
        """
        Detect anomalies in the stock price using Z-score method.
        
        Args:
            ticker (str): Stock ticker to analyze
            
        Returns:
            pd.DataFrame: Updated DataFrame with anomaly flags
        """
        data = self.fetch_data(ticker)
        if len(data) < self.window_size:
            return None
            
        close_prices = data['Close'].values
        anomalies = []
        
        for i in range(self.window_size, len(close_prices)):
            window = close_prices[i-self.window_size:i]
            current_price = close_prices[i]
            
            mean = np.mean(window)
            std = np.std(window)
            
            if std == 0:  # Avoid division by zero
                z_score = 0
            else:
                z_score = (current_price - mean) / std
                
            is_anomaly = abs(z_score) > self.threshold
            
            # Store the results
            data_point = {
                'Close': current_price,
                'Mean': mean,
                'Std': std,
                'Z-Score': z_score,
                'Anomaly': is_anomaly,
                'Time': data.index[i]
            }
            
            anomalies.append(data_point)
            
        result_df = pd.DataFrame(anomalies)
        self.history[ticker] = pd.concat([self.history[ticker], result_df], ignore_index=True)
        return result_df[result_df['Anomaly']]
    
    def monitor(self, check_interval=300):
        """
        Continuously monitor stocks for anomalies.
        
        Args:
            check_interval (int): Time between checks in seconds
        """
        print(f"Starting stock anomaly monitoring for {', '.join(self.tickers)}...")
        print(f"Checking every {check_interval//60} minutes")
        
        try:
            while True:
                for ticker in self.tickers:
                    anomalies = self.detect_anomalies(ticker)
                    if anomalies is not None and not anomalies.empty:
                        # Using ASCII art instead of Unicode emoji for Windows compatibility
                        print(f"\n!!! Anomaly detected in {ticker} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        print(anomalies[['Time', 'Close', 'Z-Score']])
                        self.send_alert(ticker, anomalies.iloc[-1])
                        self.plot_anomalies(ticker)
                
                time.sleep(check_interval)
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user.")
    
    def send_alert(self, ticker, anomaly_data):
        """
        Send email alert for detected anomaly (simulated - prints to console).
        
        Args:
            ticker (str): Stock ticker
            anomaly_data (pd.Series): Anomaly data
        """
        alert_message = (
            f"Stock Alert for {ticker}!\n\n"
            f"Anomaly detected at {anomaly_data['Time']}\n"
            f"Price: ${anomaly_data['Close']:.2f}\n"
            f"Z-Score: {anomaly_data['Z-Score']:.2f}\n"
            f"Mean: ${anomaly_data['Mean']:.2f}\n"
            f"Std Dev: ${anomaly_data['Std']:.2f}\n\n"
            f"Possible unusual activity detected!"
        )
        
        print("\n" + "="*50)
        print("ALERT EMAIL (simulated):")
        print(alert_message)
        print("="*50 + "\n")
    
    def plot_anomalies(self, ticker):
        """
        Plot the stock price with anomalies highlighted.
        
        Args:
            ticker (str): Stock ticker to plot
        """
        if len(self.history[ticker]) == 0:
            return
            
        plt.figure(figsize=(12, 6))
        df = self.history[ticker]
        
        # Plot the close price
        plt.plot(df['Time'], df['Close'], label='Close Price', color='blue', alpha=0.6)
        
        # Plot the moving average
        plt.plot(df['Time'], df['Mean'], label=f'{self.window_size}-period Mean', 
                color='green', linestyle='--', alpha=0.7)
        
        # Plot anomaly points
        anomalies = df[df['Anomaly']]
        if not anomalies.empty:
            plt.scatter(anomalies['Time'], anomalies['Close'], 
                        color='red', label='Anomaly', zorder=5)
        
        plt.title(f'Stock Price Anomalies for {ticker}')
        plt.xlabel('Time')
        plt.ylabel('Price ($)')
        plt.legend()
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    # Example usage
    monitor = StockMonitor(tickers=['AAPL', 'MSFT', 'GOOGL'], threshold=2.5)
    monitor.monitor(check_interval=300)  # Check every 5 minutes