"""Tests for links.py — URL flag logic and phone validation."""
import pytest

from app.links import check_url, check_phone


def test_blocklisted_domain_flagged():
    flags = check_url("http://paytm-kyc.in/verify")
    assert "blocklisted_domain" in flags


def test_shortener_flagged():
    flags = check_url("https://bit.ly/3xAbc")
    assert "url_shortener" in flags


def test_punycode_flagged():
    flags = check_url("https://xn--pyvt-yoa.com/bank")
    assert "punycode_idn" in flags


def test_lookalike_flagged():
    # "paytnn" is 2 edits away from "paytm"
    flags = check_url("https://paytnn.com/pay")
    assert any("lookalike" in f for f in flags)


def test_clean_url_no_flags():
    flags = check_url("https://sbi.co.in/personal")
    assert flags == []


def test_valid_phone_no_flags():
    flags = check_phone("+919876543210")
    assert flags == []


def test_invalid_phone_flagged():
    flags = check_phone("12345")
    assert "not_valid_indian_mobile" in flags

