#!/bin/bash
# Quick start script for NMS MXML Translator Helper (Linux/Mac)
# This script sets up the environment and runs the application

echo "===================================="
echo "NMS MXML Translator Helper"
echo "===================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
python -c "import PyQt6" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    echo ""
fi

# Run the application
echo "Starting application..."
echo ""
python run.py

# Deactivate virtual environment
deactivate
