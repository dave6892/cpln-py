"""Tests for the base parser module."""

from dataclasses import dataclass
from typing import Optional, Union

from cpln.parsers.base import BaseParser, preparse


class TestPreparse:
    def test_preparse_decorator(self):
        @preparse
        def test_function(cls, data):
            # Modify the data to test that a copy is passed
            data["modified"] = True
            return data

        original_data = {"original": True}
        result = test_function(None, original_data)

        # Original data should be unchanged
        assert "modified" not in original_data
        assert original_data == {"original": True}

        # Result should have the modification
        assert result["modified"] is True
        assert result["original"] is True

    def test_preparse_with_args_kwargs(self):
        @preparse
        def test_function(cls, data, extra_arg, extra_kwarg=None):
            data["extra_arg"] = extra_arg
            data["extra_kwarg"] = extra_kwarg
            return data

        original_data = {"original": True}
        result = test_function(
            None, original_data, "test_arg", extra_kwarg="test_kwarg"
        )

        assert "extra_arg" not in original_data
        assert result["extra_arg"] == "test_arg"
        assert result["extra_kwarg"] == "test_kwarg"


@dataclass
class TestParser(BaseParser):
    name: str
    value: int
    optional_field: Optional[str] = None
    nested_parser: Optional["TestNestedParser"] = None


@dataclass
class TestNestedParser(BaseParser):
    nested_name: str
    nested_value: int


class TestBaseParser:
    def test_parse_basic(self):
        data = {"name": "test", "value": 42}
        result = TestParser.parse(data)
        assert result.name == "test"
        assert result.value == 42
        assert result.optional_field is None

    def test_format_key_of_dict_default(self):
        data = {
            "camelCaseKey": "value1",
            "anotherCamelCase": "value2",
            "simple": "value3",
        }
        result = TestParser.format_key_of_dict(data)
        expected = {
            "camel_case_key": "value1",
            "another_camel_case": "value2",
            "simple": "value3",
        }
        assert result == expected

    def test_format_key_of_dict_custom_function(self):
        data = {"key1": "value1", "key2": "value2"}
        result = TestParser.format_key_of_dict(data, str.upper)
        expected = {"KEY1": "value1", "KEY2": "value2"}
        assert result == expected

    def test_to_dict_simple(self):
        parser = TestParser(name="test", value=42)
        result = parser.to_dict()
        expected = {
            "name": "test",
            "value": 42,
            "optional_field": None,
            "nested_parser": None,
        }
        assert result == expected

    def test_to_dict_with_nested_parser(self):
        nested = TestNestedParser(nested_name="nested", nested_value=10)
        parser = TestParser(name="test", value=42, nested_parser=nested)

        result = parser.to_dict()
        expected = {
            "name": "test",
            "value": 42,
            "optional_field": None,
            "nested_parser": {"nested_name": "nested", "nested_value": 10},
        }
        assert result == expected

    def test_to_dict_with_list_of_parsers(self):
        @dataclass
        class ParserWithList(BaseParser):
            items: list[TestNestedParser]
            simple_list: list[str]

        nested1 = TestNestedParser(nested_name="nested1", nested_value=1)
        nested2 = TestNestedParser(nested_name="nested2", nested_value=2)

        parser = ParserWithList(items=[nested1, nested2], simple_list=["a", "b", "c"])

        result = parser.to_dict()
        expected = {
            "items": [
                {"nested_name": "nested1", "nested_value": 1},
                {"nested_name": "nested2", "nested_value": 2},
            ],
            "simple_list": ["a", "b", "c"],
        }
        assert result == expected

    def test_pop_optional_fields(self):
        @dataclass
        class TestOptionalParser(BaseParser):
            required_field: str
            optional_field: Optional[str] = None
            union_field: Union[str, None] = None
            regular_field: int = 0

        parser = TestOptionalParser(
            required_field="test",
            optional_field="optional",
            union_field="union",
            regular_field=42,
        )

        data = {
            "required_field": "test",
            "optional_field": "optional",
            "union_field": "union",
            "regular_field": 42,
            "extra_field": "extra",
        }

        parser.pop_optional_fields(data)

        # Optional fields should be removed
        expected = {
            "required_field": "test",
            "regular_field": 42,
            "extra_field": "extra",  # Non-annotated fields remain
        }
        assert data == expected

    def test_pop_optional_fields_with_complex_union(self):
        @dataclass
        class ComplexUnionParser(BaseParser):
            required_field: str
            optional_int: Optional[int] = None
            union_str_int: Union[str, int] = ""
            none_union: Union[None, str] = None

        parser = ComplexUnionParser(required_field="test")

        data = {
            "required_field": "test",
            "optional_int": 42,
            "union_str_int": "not_optional",  # Union without None is not optional
            "none_union": "should_be_removed",
        }

        parser.pop_optional_fields(data)

        expected = {
            "required_field": "test",
            "union_str_int": "not_optional",  # Union without None stays
        }
        assert data == expected
