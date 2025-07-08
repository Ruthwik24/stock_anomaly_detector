import time
from datetime import datetime
import logging
from typing import Dict
import pandas as pd
from data_fetcher import DataFetcher
from anomaly_detector import AnomalyDetector
from alert_manager import AlertManager
from config import *

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stock_monitor.log'),
        logging.StreamHandler()
    ]
)

class StockMonitor:
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.detector = AnomalyDetector(
            window_size=WINDOW_SIZE,
            threshold=ANOMALY_THRESHOLD
        )
        self.alert_manager = AlertManager({
            'ALERT_EMAILS': ALERT_EMAILS,
            'SMTP_SERVER': SMTP_SERVER,
            'SMTP_PORT': SMTP_PORT,
            'SMTP_USER': SMTP_USER,
            'SMTP_PASSWORD': SMTP_PASSWORD
        })
        self.history: Dict[str, pd.DataFrame] = {
            ticker: pd.DataFrame(columns=['Time', 'Close', 'Mean', 'Std', 'Method', 'Anomaly'])
            for ticker in STOCKS_TO_MONITOR
        }
        self.logger = logging.getLogger('stock_monitor')

    def update_history(self, ticker: str, new_data: pd.DataFrame):
        """Update historical data for a stock"""
        if new_data is not None and not new_data.empty:
            self.history[ticker] = pd.concat(
                [self.history[ticker], new_data],
                ignore_index=True
            ).drop_duplicates(subset=['Time'])

    def monitor(self):
        """Main monitoring loop"""
        self.logger.info(f"Starting monitoring for stocks: {', '.join(STOCKS_TO_MONITOR)}")
        self.logger.info(f"Check interval: {CHECK_INTERVAL} seconds")
        
        try:
            while True:
                for ticker in STOCKS_TO_MONITOR:
                    try:
                        # Fetch and validate data
                        data = self.data_fetcher.fetch_stock_data(ticker)
                        if not self.data_fetcher.validate_data(data, ticker):
                            continue
                            
                        # Detect anomalies using multiple methods
                        zscore_results = self.detector.detect(data, method='zscore')
                        isolation_results = self.detector.detect(data, method='isolation')
                        
                        # Update history
                        self.update_history(ticker, zscore_results)
                        self.update_history(ticker, isolation_results)
                        
                        # Process alerts
                        if zscore_results is not None and not zscore_results.empty:
                            latest = zscore_results.iloc[-1]
                            self.alert_manager.console_alert(ticker, latest)
                            self.alert_manager.send_email_alert(ticker, latest, self.history[ticker])
                            
                        if isolation_results is not None and not isolation_results.empty:
                            latest = isolation_results.iloc[-1]
                            self.alert_manager.console_alert(ticker, latest)
                            self.alert_manager.send_email_alert(ticker, latest, self.history[ticker])
                            
                    except Exception as e:
                        self.logger.error(f"Error processing {ticker}: {e}")
                
                time.sleep(CHECK_INTERVAL)
                
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
        finally:
            self.logger.info("Shutting down monitor")

if __name__ == "__main__":
    monitor = StockMonitor()
    monitor.monitor()