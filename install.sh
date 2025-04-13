#!/bin/bash
# install.sh – Installer for the Skywatcher-Ryanair project (Phase 1)

set -e

echo "=== Skywatcher-Ryanair Installer ==="

# Update system packages and install required dependencies.
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y
echo "Installing Python3, pip, venv, and git..."
sudo apt install -y python3 python3-pip python3-venv git

# Create a Python virtual environment if it doesn't exist.
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment.
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip and install required Python packages.
echo "Installing required Python packages..."
pip install --upgrade pip
pip install requests twilio

# Create logs directory if it doesn't exist.
if [ ! -d "logs" ]; then
    echo "Creating logs directory..."
    mkdir logs
fi

# Optionally, copy a sample config file if one doesn't exist.
if [ ! -f "config/config.ini" ]; then
    echo "Creating default config file at config/config.ini..."
    mkdir -p config
    cat <<EOL > config/config.ini
[twilio]
account_sid = YOUR_TWILIO_SID
auth_token = YOUR_TWILIO_AUTH_TOKEN
from_number = YOUR_TWILIO_WHATSAPP_NUMBER
to_number = YOUR_PERSONAL_WHATSAPP_NUMBER

[location]
latitude = -38.083119
longitude = 144.064841
EOL
    echo "Please update the config/config.ini file with your actual credentials."
fi

# Set up the systemd service.
SERVICE_FILE="/etc/systemd/system/skywatcher.service"
echo "Configuring systemd service at ${SERVICE_FILE}..."

sudo bash -c "cat > ${SERVICE_FILE}" <<EOF
[Unit]
Description=Skywatcher-Ryanair Service
After=network.target

[Service]
User=$(whoami)
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python $(pwd)/skywatcher.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "Enabling skywatcher service to start at boot..."
sudo systemctl enable skywatcher.service

echo "Installation complete!"
echo "To start the service now, run: sudo systemctl start skywatcher.service"
echo "To check status: sudo systemctl status skywatcher.service"

# Deactivate the virtual environment.
deactivate
