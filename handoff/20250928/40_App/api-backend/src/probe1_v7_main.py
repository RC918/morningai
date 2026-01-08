from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route('/probe', methods=['POST'])
def probe():
    data = request.get_json()
    result = process_data(data)
    return jsonify(result)

def process_data(data):
    # Simulate processing
    return {"status": "success", "data": data}