import os

# Ensure all environment variables used are defined
API_KEY = os.getenv("API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
DEBUG_MODE = os.getenv("DEBUG_MODE")

def configure_app():
    config = {
        "API_KEY": API_KEY,
        "DATABASE_URL": DATABASE_URL,
        "DEBUG_MODE": DEBUG_MODE,
    }
    return config