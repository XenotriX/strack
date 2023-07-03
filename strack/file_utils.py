from .data import Data


DATA_FILE = ''


def set_file(file):
    global DATA_FILE
    DATA_FILE = file


def load_file() -> Data:
    try:
        with open(DATA_FILE) as f:
            data = Data.from_file(f)
    except FileNotFoundError:
        data = Data()

    return data


def save_file(data):
    with open(DATA_FILE, 'w') as f:
        data.to_file(f)
