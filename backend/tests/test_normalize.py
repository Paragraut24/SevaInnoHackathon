from app.normalize import detect_script, extract_phones, extract_urls, normalize_text


def test_normalize_devanagari_digits_and_zero_width():
    assert normalize_text("कॉल  करा \u200b९८७६५४३२१०") == "कॉल करा 9876543210"


def test_normalize_lowercases_latin_and_collapses_space():
    assert normalize_text("  URGENT \n  Call  NOW ") == "urgent call now"


def test_detect_script():
    assert detect_script("तुमचे खाते बंद झाले आहे") == "deva"
    assert detect_script("Your account is blocked") == "latin"
    assert detect_script("तुमचे SBI खाते KYC pending आहे") == "mixed"
    assert detect_script("12345 !!!") == "latin"


def test_extract_urls_scheme_bare_and_shortener():
    text = "Visit http://bit.ly/abc, or sbi-kyc.xyz/login and t.me/crypto_king. Mail a@b.com"
    assert extract_urls(text) == ["http://bit.ly/abc", "sbi-kyc.xyz/login", "t.me/crypto_king"]


def test_extract_urls_dedupes():
    assert extract_urls("go to loan-fast.in now, loan-fast.in") == ["loan-fast.in"]


def test_extract_phones_formats():
    text = "Call +91 98765 43210 or 098123-45678 or 9123456789 or ९८१२३४५६७८"
    assert extract_phones(text) == ["9876543210", "9812345678", "9123456789"]


def test_extract_phones_rejects_non_mobile_and_long_numbers():
    assert extract_phones("OTP 482910, ref 4588915399, order 12345") == []
    assert extract_phones("123456789012") == []

