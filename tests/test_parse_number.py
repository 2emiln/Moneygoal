from moneygoal.io.avanza_csv import parse_number

def test_parse_number_basic():
    assert parse_number("1,23") == 1.23
    assert parse_number("123") == 123.0
    assert parse_number("-363 546,05") == -363546.05