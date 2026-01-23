def calculate_balance(income, expenses):
    return income - expenses


def calculate_saving_rate(income, savings):
    if income <= 0:
        return 0
    return round((savings / income) * 100, 2)


def test_calculate_balance():
    assert calculate_balance(2000, 1500) == 500
    assert calculate_balance(1000, 1000) == 0
    assert calculate_balance(800, 1000) == -200


def test_calculate_saving_rate():
    assert calculate_saving_rate(2000, 400) == 20.0
    assert calculate_saving_rate(1000, 0) == 0.0
    assert calculate_saving_rate(0, 200) == 0
