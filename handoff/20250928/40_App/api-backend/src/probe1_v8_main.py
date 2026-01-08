# handoff/20250928/40_App/api-backend/src/probe1_v8_main.py

import json
import logging
import time
# Remove the unused 'sys' import below
# import sys
from flask import Flask, request

app = Flask(__name__)

@app.route('/probe', methods=['GET'])
def probe():
    return json.dumps({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)