#!/bin/bash

VENV_NAME="venv"
VENV_PATH="./$VENV_NAME"

# Set up the CAN interface
sudo ip link set can0 down
sudo ip link set can0 type can bitrate 100000
sudo ip link set can0 up

# Navigate to the directory where your Python script is located
cd /pi-canbus-tranceiver

# Check the virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Creating virtual environment..."
    sudo python -m venv "$VENV_NAME" || { echo "Failed to create virtual environment"; exit 1; }
fi

# Activate the virtual environment
echo "Activating environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install python-can

# Run the Python receive script
echo "Running tranceiver..."
python can_transceiver.py
