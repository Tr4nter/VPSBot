import json


def get_json(filename):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        with open(filename, "w") as f:
            json.dump({}, f)
        return {}


def save_json(data: dict, filePath: str) -> bool:
    with open(filePath, 'w') as f:
        json.dump(data, f, indent=4)
    return True
