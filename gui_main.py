#!/usr/bin/env python3
"""
🎨 Ed's AI Interface — Desktop GUI Application.
Launch the AI agent with a beautiful Windows desktop chat interface.
"""

import sys
import os

# Ensure the project root is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.gui import launch_gui

if __name__ == "__main__":
    launch_gui()
