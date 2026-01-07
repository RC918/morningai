# handoff/20250928/40_App/api-backend/src/probe0_lint_error_v3.py

def calculate_probe_data(data):
    intermediate_value = process_data(data)
    final_result = intermediate_value * 2
    return final_result

def process_data(data):
    processed = data + 10
    return processed

data_input = 5
output = calculate_probe_data(data_input)
print(output)