import json
import os
import tempfile


def save_data(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def load_data(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_save_and_load_data():
    test_data = {
        "month": "2025-01",
        "income": 2000,
        "expenses": 1500
    }

    with tempfile.TemporaryDirectory() as tmp:
        file_path = os.path.join(tmp, "test.json")

        save_data(file_path, test_data)
        loaded_data = load_data(file_path)

        assert loaded_data == test_data
