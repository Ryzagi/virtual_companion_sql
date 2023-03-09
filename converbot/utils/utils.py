import json


def read_json_file(file_path):
    # Open the file
    with open(file_path, "r") as file:
        # Load the JSON data
        data = json.load(file)
        # return the data
        return data
