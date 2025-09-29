#!/usr/bin/env python3
"""
Development server runner for Morning AI API
"""
import os
import sys
from pathlib import Path

src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / "src" / ".env")

from main import app

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
