"""
Tests for utility functions.
"""

from examples.utils import safe_get_attr


class TestObject:
    """Test class with attributes in different case formats."""

    def __init__(self):
        self.camelCase = "camel"
        self.snake_case = "snake"
        self.TitleCase = "title"
        self.original = "original"


def test_safe_get_attr_original():
    """Test getting attribute in original format."""
    obj = TestObject()
    assert safe_get_attr(obj, "original") == "original"


def test_safe_get_attr_camel_case():
    """Test getting attribute in camelCase format."""
    obj = TestObject()
    assert safe_get_attr(obj, "camel_case") == "camel"
    assert safe_get_attr(obj, "camelCase") == "camel"


def test_safe_get_attr_snake_case():
    """Test getting attribute in snake_case format."""
    obj = TestObject()
    assert safe_get_attr(obj, "snakeCase") == "snake"
    assert safe_get_attr(obj, "snake_case") == "snake"


def test_safe_get_attr_title_case():
    """Test getting attribute in TitleCase format."""
    obj = TestObject()
    assert safe_get_attr(obj, "title_case") == "title"
    assert safe_get_attr(obj, "TitleCase") == "title"


def test_safe_get_attr_default():
    """Test getting non-existent attribute returns default value."""
    obj = TestObject()
    assert safe_get_attr(obj, "non_existent") == "N/A"
    assert safe_get_attr(obj, "nonExistent") == "N/A"
    assert safe_get_attr(obj, "NonExistent") == "N/A"


def test_safe_get_attr_custom_default():
    """Test getting non-existent attribute with custom default value."""
    obj = TestObject()
    assert safe_get_attr(obj, "non_existent", default="custom") == "custom"


def test_safe_get_attr_none_value():
    """Test getting attribute that exists but has None value."""
    obj = TestObject()
    obj.none_value = None
    assert safe_get_attr(obj, "none_value") == "None"
    assert safe_get_attr(obj, "noneValue") == "None"


def test_safe_get_attr_complex_object():
    """Test getting attribute with complex object value."""
    obj = TestObject()
    obj.complex = {"key": "value"}
    assert safe_get_attr(obj, "complex") == "{'key': 'value'}"
    assert safe_get_attr(obj, "Complex") == "{'key': 'value'}"


def test_safe_get_attr_empty_string():
    """Test getting attribute with empty string value."""
    obj = TestObject()
    obj.empty = ""
    assert safe_get_attr(obj, "empty") == ""
    assert safe_get_attr(obj, "Empty") == ""


def test_safe_get_attr_special_chars():
    """Test getting attribute with special characters in name."""
    obj = TestObject()
    obj.special_chars = "special"
    assert safe_get_attr(obj, "special-chars") == "special"
    assert safe_get_attr(obj, "specialChars") == "special"
    assert safe_get_attr(obj, "SpecialChars") == "special"
