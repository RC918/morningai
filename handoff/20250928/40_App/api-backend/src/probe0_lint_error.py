import json

try:
    with open('planner_runs.jsonl', 'r') as file:
        lines = file.readlines()
        for line in lines:
            data = json.loads(line)
except json.JSONDecodeError:
    print("Invalid JSON")