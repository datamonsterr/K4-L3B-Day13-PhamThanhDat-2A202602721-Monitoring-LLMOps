from app.pii import scrub_text


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_common_vietnamese_phone_formats() -> None:
    phone_numbers = (
        "0901234567",
        "090 123 4567",
        "090.123.4567",
        "090-123-4567",
        "+84 90 123 4567",
    )

    for phone_number in phone_numbers:
        out = scrub_text(f"Contact: {phone_number}")
        assert phone_number not in out
        assert "REDACTED_PHONE_VN" in out

def test_scrub_cccd_format() -> None:
    cccd_numbers = (
        "001204022755",
        "012345678901",
        "031234567891"
    )

    for cccd_number in cccd_numbers:
        out = scrub_text(f"CCCD: {cccd_number}")
        assert cccd_number not in out
        assert "REDACTED_CCCD" in out

def test_scrub_credit_card_format() -> None:
    credit_card_numbers = (
        "1234567890123456",
        "5109403243823493",
    )

    for credit_card_number in credit_card_numbers:
        out = scrub_text(f"Credit Card: {credit_card_number}")
        assert credit_card_number not in out
        assert "REDACTED_CREDIT_CARD" in out
