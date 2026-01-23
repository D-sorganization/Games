#!/bin/bash
# Launcher script for Wizard of Wor

echo "Starting Wizard of Wor..."

# Check if pygame is installed
python3 -c "import pygame" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Pygame not found. Installing..."
    pip install -r requirements.txt
fi

# Run the game
python3 game.py
