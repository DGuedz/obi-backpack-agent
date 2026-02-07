#!/bin/bash

echo "========================================="
echo "   OBI OPERATING SYSTEM - INSTALLATION   "
echo "========================================="
echo ""

# 1. Check Python
if ! command -v python3 &> /dev/null
then
    echo "❌ Python 3 could not be found. Please install Python 3."
    exit 1
fi

echo "✅ Python 3 detected."

# 2. Create Virtual Environment
echo "📦 Creating virtual environment (obi_env)..."
python3 -m venv obi_env

# 3. Activate and Install
echo "⬇️ Installing dependencies..."
source obi_env/bin/activate

# Create dummy requirements if not exists, or install core libs directly
pip install requests pandas ccxt termcolor

echo ""
echo "========================================="
echo "✅ OBI CORE INSTALLED SUCCESSFULLY!"
echo "========================================="
echo ""
echo "To start the OBI Console:"
echo "1. source obi_env/bin/activate"
echo "2. python3 obiwork_core/gatekeeper/wallet_tracker.py --help"
echo ""
echo "Welcome to the Resistance."
