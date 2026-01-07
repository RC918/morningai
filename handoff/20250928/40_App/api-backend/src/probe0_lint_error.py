import json,os 

def load_config(filename):
    with open(filename) as json_file:
        data = json.load(json_file)
    return data

data = load_config( "config.json" )
print (data)