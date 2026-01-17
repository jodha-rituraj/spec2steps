#!/bin/bash

# Setup script for AI Automation From Requirements
# This script creates a virtual environment and installs all dependencies

set -e  # Exit on error

echo "🚀 Setting up AI Automation From Requirements..."
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "📋 Detected Python version: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created!"
else
    echo "ℹ️  Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip --quiet

# Install requirements
echo "📥 Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ .env file created from .env.example"
        echo "⚠️  Please edit .env file and add your GROQ_API_KEY"
    elif [ -f "ENV_TEMPLATE.txt" ]; then
        cp ENV_TEMPLATE.txt .env
        echo "✅ .env file created from ENV_TEMPLATE.txt"
        echo "⚠️  Please edit .env file and add your GROQ_API_KEY"
    else
        echo "GROQ_API_KEY=your_api_key_here" > .env
        echo "✅ .env file created with placeholder"
        echo "⚠️  Please edit .env file and add your GROQ_API_KEY"
    fi
else
    echo "ℹ️  .env file already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source .venv/bin/activate"
echo ""
echo "To run the application, run:"
echo "  streamlit run app.py"
echo ""
echo "To deactivate the virtual environment, run:"
echo "  deactivate"
echo ""
