import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from datetime import datetime
import logging

class AlertManager:
    def __init__(self, email_config):
        self.email_config = email_config
        self.logger = logging.getLogger('alert_manager')

    def generate_alert_message(self, ticker, anomaly_data):
        """Generate formatted alert message"""
        return (
            f"Stock Alert for {ticker}!\n\n"
            f"Anomaly detected at {anomaly_data['Time']}\n"
            f"Price: ${anomaly_data['Close']:.2f}\n"
            f"Detection Method: {anomaly_data['Method']}\n"
            f"Mean: ${anomaly_data.get('Mean', 'N/A'):.2f}\n"
            f"Std Dev: ${anomaly_data.get('Std', 'N/A'):.2f}\n\n"
            f"Possible unusual activity detected!"
        )

    def create_plot(self, ticker, history):
        """Create plot of stock prices with anomalies"""
        plt.figure(figsize=(12, 6))
        plt.plot(history['Time'], history['Close'], label='Close Price', color='blue', alpha=0.6)
        
        if 'Mean' in history.columns:
            plt.plot(history['Time'], history['Mean'], label='Moving Mean', 
                    color='green', linestyle='--', alpha=0.7)
        
        anomalies = history[history['Anomaly']]
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
        
        # Save plot to bytes
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        plt.close()
        return buffer

    def send_email_alert(self, ticker, anomaly_data, history):
        """Send email alert with plot attachment"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['SMTP_USER']
            msg['To'] = ", ".join(self.email_config['ALERT_EMAILS'])
            msg['Subject'] = f"Stock Anomaly Alert: {ticker}"
            
            # Create text and HTML versions
            text = self.generate_alert_message(ticker, anomaly_data)
            html = f"""\
            <html>
              <body>
                <p>{text.replace('\n', '<br>')}</p>
                <img src="cid:plot" alt="Stock Chart">
              </body>
            </html>
            """
            
            # Attach text version
            msg.attach(MIMEText(text, 'plain'))
            
            # Attach HTML version
            part = MIMEText(html, 'html')
            msg.attach(part)
            
            # Attach plot image
            plot_buffer = self.create_plot(ticker, history)
            image = MIMEText(plot_buffer.read(), 'base64', 'png')
            image.add_header('Content-ID', '<plot>')
            image.add_header('Content-Disposition', 'inline', filename='plot.png')
            msg.attach(image)
            
            # Send email
            with smtplib.SMTP(self.email_config['SMTP_SERVER'], self.email_config['SMTP_PORT']) as server:
                server.starttls()
                server.login(self.email_config['SMTP_USER'], self.email_config['SMTP_PASSWORD'])
                server.send_message(msg)
                
            self.logger.info(f"Email alert sent for {ticker}")
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")

    def console_alert(self, ticker, anomaly_data):
        """Print alert to console"""
        print("\n" + "="*50)
        print("STOCK ALERT:")
        print(self.generate_alert_message(ticker, anomaly_data))
        print("="*50 + "\n")