# handoff/20250928/40_App/api-backend/src/probe3_advanced_syntax_trap.py

def calculate_sum(a, b):
    result = a + b
    return result

def process_data(data):
    total = 0
    for item in data:
        total += item
    return total

data_list = [1, 2, 3, 4, 5]
output = process_data(data_list)
print(output)