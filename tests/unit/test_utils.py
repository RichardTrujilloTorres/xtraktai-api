"""
Unit tests for utility functions
"""
import pytest
from app.utils import (
    parse_date,
    parse_time,
    extract_amount,
    format_currency,
    clean_text,
    validate_file_size,
)


class TestParseDate:
    """Tests for parse_date function"""

    def test_iso_format(self):
        """Parse ISO format YYYY-MM-DD"""
        assert parse_date("2024-12-05") == "2024-12-05"

    def test_us_format_slash(self):
        """Parse US format MM/DD/YYYY"""
        assert parse_date("12/05/2024") == "2024-12-05"

    def test_eu_format_slash(self):
        """Parse EU format DD/MM/YYYY (unambiguous date)"""
        # Use day > 12 to avoid ambiguity with US format
        assert parse_date("31/12/2024") == "2024-12-31"

    def test_us_format_dash(self):
        """Parse US format MM-DD-YYYY"""
        assert parse_date("12-05-2024") == "2024-12-05"

    def test_long_month_format(self):
        """Parse format with full month name"""
        assert parse_date("December 05, 2024") == "2024-12-05"

    def test_short_month_format(self):
        """Parse format with abbreviated month"""
        assert parse_date("Dec 05, 2024") == "2024-12-05"

    def test_day_first_long_month(self):
        """Parse format DD Month YYYY"""
        assert parse_date("05 December 2024") == "2024-12-05"

    def test_day_first_short_month(self):
        """Parse format DD Mon YYYY"""
        assert parse_date("05 Dec 2024") == "2024-12-05"

    def test_with_whitespace(self):
        """Parse date with leading/trailing whitespace"""
        assert parse_date("  2024-12-05  ") == "2024-12-05"

    def test_empty_string(self):
        """Empty string returns None"""
        assert parse_date("") is None

    def test_none_input(self):
        """None input returns None"""
        assert parse_date(None) is None

    def test_invalid_format(self):
        """Unrecognized format returns None"""
        assert parse_date("not a date") is None
        assert parse_date("2024/12/05") is None  # Not in supported formats


class TestParseTime:
    """Tests for parse_time function"""

    def test_24_hour_format(self):
        """Parse 24-hour format HH:MM"""
        assert parse_time("14:30") == "14:30"

    def test_24_hour_with_seconds(self):
        """Parse 24-hour format with seconds"""
        assert parse_time("14:30:45") == "14:30"

    def test_12_hour_pm(self):
        """Parse 12-hour PM format"""
        assert parse_time("02:30 PM") == "14:30"

    def test_12_hour_am(self):
        """Parse 12-hour AM format"""
        assert parse_time("09:15 AM") == "09:15"

    def test_12_hour_with_seconds(self):
        """Parse 12-hour format with seconds"""
        assert parse_time("02:30:00 PM") == "14:30"

    def test_with_whitespace(self):
        """Parse time with whitespace"""
        assert parse_time("  14:30  ") == "14:30"

    def test_empty_string(self):
        """Empty string returns None"""
        assert parse_time("") is None

    def test_none_input(self):
        """None input returns None"""
        assert parse_time(None) is None

    def test_invalid_format(self):
        """Unrecognized format returns None"""
        assert parse_time("not a time") is None


class TestExtractAmount:
    """Tests for extract_amount function"""

    def test_plain_number(self):
        """Extract plain number"""
        assert extract_amount("25.99") == 25.99

    def test_with_dollar_sign(self):
        """Extract amount with $"""
        assert extract_amount("$25.99") == 25.99

    def test_with_euro_sign(self):
        """Extract amount with €"""
        assert extract_amount("€25.99") == 25.99

    def test_with_pound_sign(self):
        """Extract amount with £"""
        assert extract_amount("£25.99") == 25.99

    def test_with_comma_thousands(self):
        """Extract amount with comma separator"""
        assert extract_amount("$1,234.56") == 1234.56

    def test_with_whitespace(self):
        """Extract amount with whitespace"""
        assert extract_amount("$ 25.99") == 25.99

    def test_integer(self):
        """Extract whole number"""
        assert extract_amount("$100") == 100.0

    def test_empty_string(self):
        """Empty string returns None"""
        assert extract_amount("") is None

    def test_none_input(self):
        """None input returns None"""
        assert extract_amount(None) is None

    def test_invalid_format(self):
        """Non-numeric string returns None"""
        assert extract_amount("not a number") is None


class TestFormatCurrency:
    """Tests for format_currency function"""

    def test_usd(self):
        """Format as USD"""
        assert format_currency(25.99, "USD") == "$25.99"

    def test_eur(self):
        """Format as EUR"""
        assert format_currency(25.99, "EUR") == "€25.99"

    def test_gbp(self):
        """Format as GBP"""
        assert format_currency(25.99, "GBP") == "£25.99"

    def test_jpy(self):
        """Format as JPY"""
        assert format_currency(1000, "JPY") == "¥1000.00"

    def test_unknown_currency(self):
        """Unknown currency uses code as symbol"""
        assert format_currency(25.99, "CHF") == "CHF25.99"

    def test_default_currency(self):
        """Default currency is USD"""
        assert format_currency(25.99) == "$25.99"

    def test_rounds_to_two_decimals(self):
        """Amount is rounded to 2 decimal places"""
        assert format_currency(25.999, "USD") == "$26.00"
        assert format_currency(25.994, "USD") == "$25.99"

    def test_zero_amount(self):
        """Zero amount formats correctly"""
        assert format_currency(0, "USD") == "$0.00"


class TestCleanText:
    """Tests for clean_text function"""

    def test_removes_extra_whitespace(self):
        """Collapse multiple spaces to single space"""
        assert clean_text("hello    world") == "hello world"

    def test_removes_newlines(self):
        """Convert newlines to spaces"""
        assert clean_text("hello\nworld") == "hello world"

    def test_removes_tabs(self):
        """Convert tabs to spaces"""
        assert clean_text("hello\tworld") == "hello world"

    def test_preserves_basic_punctuation(self):
        """Keep common punctuation"""
        assert clean_text("Hello, world!") == "Hello, world!"
        assert clean_text("Price: $25.99") == "Price: 25.99"  # $ is removed

    def test_removes_special_characters(self):
        """Remove unusual special characters"""
        assert clean_text("Hello™ World®") == "Hello World"

    def test_preserves_parentheses(self):
        """Keep parentheses"""
        assert clean_text("Item (2 pack)") == "Item (2 pack)"

    def test_preserves_at_symbol(self):
        """Keep @ symbol"""
        assert clean_text("2 @ $5.00") == "2 @ 5.00"

    def test_strips_leading_trailing(self):
        """Strip whitespace from ends"""
        assert clean_text("  hello world  ") == "hello world"

    def test_empty_string(self):
        """Empty string returns empty string"""
        assert clean_text("") == ""

    def test_none_input(self):
        """None input returns empty string"""
        assert clean_text(None) == ""


class TestValidateFileSize:
    """Tests for validate_file_size function"""

    def test_small_file_valid(self):
        """Small file passes validation"""
        assert validate_file_size(1024) is True  # 1 KB

    def test_exactly_at_limit(self):
        """File exactly at limit passes"""
        assert validate_file_size(10 * 1024 * 1024) is True  # 10 MB

    def test_over_limit(self):
        """File over limit fails"""
        assert validate_file_size(11 * 1024 * 1024) is False  # 11 MB

    def test_custom_limit(self):
        """Custom size limit works"""
        assert validate_file_size(5 * 1024 * 1024, max_size_mb=5) is True
        assert validate_file_size(6 * 1024 * 1024, max_size_mb=5) is False

    def test_zero_size(self):
        """Zero size file passes"""
        assert validate_file_size(0) is True

    def test_large_limit(self):
        """Large custom limit works"""
        assert validate_file_size(50 * 1024 * 1024, max_size_mb=100) is True
