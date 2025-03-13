#!/bin/bash

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 to run this application."
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "UV is not installed. Please install UV package manager:"
    echo "  curl -sSf https://astral.sh/uv/install.sh | sh"
    echo "Or visit https://github.com/astral-sh/uv for installation instructions."
    exit 1
fi

# Check if virtual environment exists, create if not
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment using UV..."
    uv venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies using UV..."
uv pip install -r requirements.txt

# Run the application
echo "Starting Flask application on http://localhost:5000"
python app.py 