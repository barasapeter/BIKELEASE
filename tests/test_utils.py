from utils import normalize_and_validate_phone_number_ke, phone_number_is_valid


import pytest


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("0712345678", "254712345678"),
        ("712345678", "254712345678"),
        ("254712345678", "254712345678"),
        ("+254 712 345 678", "254712345678"),
        ("(0712) 345-678", "254712345678"),
        (
            "0112345678",
            "254112345678",
        ),
    ],
)
def test_normalize_valid_numbers(raw, expected):
    assert normalize_and_validate_phone_number_ke(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        None,
        "",
        "foo",
        "123",
        "254812345678",
        "25471234567",
        "2547123456789",
        "071234567",
        "0812345678",
    ],
)
def test_normalize_invalid_numbers_raise(raw):
    with pytest.raises(ValueError):
        normalize_and_validate_phone_number_ke(raw)


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("0712345678", True),
        ("254812345678", False),
        (None, False),
    ],
)
def test_phone_number_is_valid(raw, expected):
    assert phone_number_is_valid(raw) is expected
