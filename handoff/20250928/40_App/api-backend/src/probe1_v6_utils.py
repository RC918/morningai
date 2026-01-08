# handoff/20250928/40_App/api-backend/src/probe1_v6_utils.py

def process_data(data):
    temp = data.get('temperature')
    if temp is not None:
        print(f"Temperature: {temp}")
    return data