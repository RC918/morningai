import json

def parse_json(json_string):
    parsed_json = json.loads(json_string)
    return parsed_json

json_string = '{"name": "John", "age": 30, "city": "New York"}'
print(parse_json(json_string))