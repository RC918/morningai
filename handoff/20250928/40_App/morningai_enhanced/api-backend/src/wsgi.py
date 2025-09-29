"""
WSGI entry point for production deployment
"""
import os
import sys
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from dotenv import load_dotenv
load_dotenv(current_dir / ".env")

from main import app

if __name__ == "__main__":
    app.run()
