import os
import time
import requests
import logging
from datetime import datetime, timedelta
from twilio.rest import Client
from configparser import ConfigParser

# Load configuration from config/config.ini
config = ConfigParser()
config.read('config/config.ini')

# Twilio configuration
TWILIO_SID = config['twilio']['account_sid']
TWILIO_TOKEN = config['twilio']['auth_token']
TWILIO_FROM = config['twilio']['from_number']
TWILIO_TO = config['twilio']['to_number']

# Location configuration (latitude/longitude)
LAT = float(config['location']['latitude'])
LON = float(config['location']['longitude'])

# Set up logging - ensure the logs directory exists before writing
log_dir = 'logs'
if not os.path.isdir(log_dir):
    os.makedirs(log_dir)
logging.basicConfig(filename=os.path.join(log_dir, 'detections.log'),
                    level=logging.INFO,
                    format='%(asctime)s - %(message)s')

# Function to send WhatsApp message via Twilio
def send_whatsapp_message(message):
    try:
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        client.messages.create(
            body=message,
            from_=f'whatsapp:{TWILIO_FROM}',
            to=f'whatsapp:{TWILIO_TO}'
        )
        logging.info("WhatsApp message sent successfully.")
    except Exception as e:
        logging.error(f"Error sending WhatsApp message: {e}")

# Function to fetch nearby aircraft using the ADS-B Exchange API
def get_planes_overhead(lat, lon, radius_km=25):
    try:
        # Construct the URL with the given parameters
        url = f'https://public-api.adsbexchange.com/VirtualRadar/AircraftList.json?lat={lat}&lng={lon}&fDstL=0&fDstU={radius_km}'
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        planes = data.get('acList', [])
        return planes
    except Exception as e:
        logging.error(f"Error fetching aircraft data: {e}")
        return []

# Function to filter for Ryanair flights and send alerts
def detect_ryanair():
    planes = get_planes_overhead(LAT, LON)
    for plane in planes:
        operator = plane.get('Op', '')
        # Check if the operator indicates Ryanair (case insensitive match)
        if 'ryanair' in operator.lower():
            flight = plane.get('Call', 'Unknown')
            from_airport = plane.get('From', '---')
            to_airport = plane.get('To', '---')
            aircraft_type = plane.get('Type', 'Unknown')
            # The 'PosTime' field is in milliseconds; convert to seconds if possible.
            pos_time = plane.get('PosTime', 0)
            try:
                seen = datetime.utcnow() - timedelta(seconds=int(pos_time) / 1000)
            except Exception:
                seen = datetime.utcnow()
            msg = (
                f"🛫 Ryanair flight detected!\n\n"
                f"Flight: {flight}\n"
                f"Type: {aircraft_type}\n"
                f"From: {from_airport}\n"
                f"To: {to_airport}\n"
                f"Seen: {seen.strftime('%H:%M:%S UTC')}"
            )
            # Send WhatsApp alert via Twilio
            send_whatsapp_message(msg)
            # Log the detection
            logging.info(f"Detected Ryanair flight: {msg}")

if __name__ == "__main__":
    detect_ryanair()
