# handoff/20250928/40_App/api-backend/src/probe1_v6_utils.py

def process_data(data):
    processed = []
    for item in data:
        if item > 10:
            processed.append(item * 2)
        else:
            processed.append(item + 5)
    undefined_val = 0  # Fix: Define the undefined variable
    return sum(processed) + undefined_val