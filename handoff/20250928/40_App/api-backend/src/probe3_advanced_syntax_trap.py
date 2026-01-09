# handoff/20250928/40_App/api-backend/src/probe3_advanced_syntax_trap.py

def calculate_sum(a, b):
    result = a + b
    return result

def process_data(data):
    total = 0
    for item in data:
        value = item.get('value', 0)
        total += value
    return total

# Lint error: F841 unused variable 'unused_var'
def example_function():
    used_var = 42
    print(used_var)

example_function()