"""Tests for base parser module following unit testing best practices."""

import unittest
from dataclasses import dataclass
from typing import Optional, Union

from cpln.parsers.base import BaseParser, preparse


class TestPreparseDecorator(unittest.TestCase):
    """Test @preparse decorator functionality"""

    def test_preparse_decorator_creates_copy_of_input_data(self):
        """Test that @preparse decorator passes a copy of data, not original"""

        # Arrange
        @preparse
        def test_function(cls, data):
            # Modify the data to test that a copy is passed
            data["modified"] = True
            return data

        original_data = {"original": True}

        # Act
        result = test_function(None, original_data)

        # Assert
        # Original data should be unchanged
        self.assertNotIn("modified", original_data)
        self.assertEqual(original_data, {"original": True})

        # Result should have the modification
        self.assertIn("modified", result)
        self.assertTrue(result["modified"])
        self.assertTrue(result["original"])

    def test_preparse_decorator_preserves_function_signature_with_args_kwargs(self):
        """Test that @preparse decorator works with additional args and kwargs"""

        # Arrange
        @preparse
        def test_function_with_params(cls, data, extra_arg, extra_kwarg=None):
            data["extra_arg"] = extra_arg
            data["extra_kwarg"] = extra_kwarg
            return data

        original_data = {"original": True}

        # Act
        result = test_function_with_params(
            None, original_data, "test_arg", extra_kwarg="test_kwarg"
        )

        # Assert
        # Original data should be unchanged
        self.assertNotIn("extra_arg", original_data)
        self.assertEqual(original_data, {"original": True})

        # Result should contain the parameters
        self.assertEqual(result["extra_arg"], "test_arg")
        self.assertEqual(result["extra_kwarg"], "test_kwarg")

    def test_preparse_decorator_handles_empty_data_dictionary(self):
        """Test that @preparse decorator handles empty data dictionary"""

        # Arrange
        @preparse
        def test_function_empty(cls, data):
            data["added"] = "new_value"
            return data

        original_data = {}

        # Act
        result = test_function_empty(None, original_data)

        # Assert
        self.assertEqual(original_data, {})  # Original should remain empty
        self.assertEqual(result, {"added": "new_value"})

    def test_preparse_decorator_with_nested_data_structures_creates_shallow_copy(self):
        """Test that @preparse decorator creates shallow copy of nested structures"""

        # Arrange
        @preparse
        def test_function_nested(cls, data):
            data["new_key"] = "new_value"
            # Modify nested structure to test shallow copy behavior
            if "nested" in data:
                data["nested"]["modified"] = True
            return data

        original_data = {"top_level": True, "nested": {"inner": "value"}}

        # Act
        _ = test_function_nested(None, original_data)

        # Assert
        # Top-level original data should not have new_key
        self.assertNotIn("new_key", original_data)
        # But nested objects are shallow copied, so modifications affect original
        self.assertTrue(original_data["nested"]["modified"])  # type: ignore


@dataclass
class TestParser(BaseParser):
    """Test parser class for testing BaseParser functionality"""

    name: str
    value: int
    optional_field: Optional[str] = None
    nested_parser: Optional["TestNestedParser"] = None


@dataclass
class TestNestedParser(BaseParser):
    """Test nested parser class"""

    nested_name: str
    nested_value: int


class TestBaseParserParseMethod(unittest.TestCase):
    """Test BaseParser.parse() method"""

    def test_parse_with_basic_data_creates_parser_instance(self):
        """Test that parse() creates parser instance from basic data"""
        # Arrange
        data = {"name": "test_parser", "value": 42}

        # Act
        result = TestParser.parse(data)

        # Assert
        self.assertIsInstance(result, TestParser)
        self.assertEqual(result.name, "test_parser")
        self.assertEqual(result.value, 42)
        self.assertIsNone(result.optional_field)

    def test_parse_with_all_fields_creates_complete_parser_instance(self):
        """Test that parse() creates complete parser instance with all fields"""
        # Arrange
        data = {
            "name": "complete_parser",
            "value": 100,
            "optional_field": "optional_value",
        }

        # Act
        result = TestParser.parse(data)

        # Assert
        self.assertIsInstance(result, TestParser)
        self.assertEqual(result.name, "complete_parser")
        self.assertEqual(result.value, 100)
        self.assertEqual(result.optional_field, "optional_value")

    def test_parse_with_extra_fields_ignores_extra_data(self):
        """Test that parse() ignores fields not in the dataclass"""
        # Arrange
        data = {
            "name": "parser_with_extra",
            "value": 200,
            "extra_field": "should_be_ignored",
            "another_extra": 999,
        }

        # Act
        result = TestParser.parse(data)

        # Assert
        self.assertIsInstance(result, TestParser)
        self.assertEqual(result.name, "parser_with_extra")
        self.assertEqual(result.value, 200)
        # Extra fields should not appear as attributes
        self.assertFalse(hasattr(result, "extra_field"))
        self.assertFalse(hasattr(result, "another_extra"))

    def test_parse_with_missing_required_field_raises_type_error(self):
        """Test that parse() raises TypeError when required fields are missing"""
        # Arrange
        incomplete_data_cases = [
            {"name": "missing_value"},  # Missing value field
            {"value": 42},  # Missing name field
            {},  # Missing both required fields
        ]

        for data in incomplete_data_cases:
            # Act & Assert
            with self.subTest(data=data), self.assertRaises(TypeError):
                TestParser.parse(data)


class TestBaseParserFormatKeyOfDict(unittest.TestCase):
    """Test BaseParser.format_key_of_dict() method"""

    def test_format_key_of_dict_with_default_underscore_converts_camel_case(self):
        """Test that format_key_of_dict converts camelCase to snake_case by default"""
        # Arrange
        data = {
            "camelCaseKey": "value1",
            "anotherCamelCase": "value2",
            "simpleKey": "value3",
            "XMLHttpRequest": "value4",
        }

        # Act
        result = TestParser.format_key_of_dict(data)

        # Assert
        expected = {
            "camel_case_key": "value1",
            "another_camel_case": "value2",
            "simple_key": "value3",
            "xml_http_request": "value4",
        }
        self.assertEqual(result, expected)

    def test_format_key_of_dict_with_custom_format_function_applies_custom_transformation(
        self,
    ):
        """Test that format_key_of_dict accepts custom format functions"""
        # Arrange
        data = {"key1": "value1", "key2": "value2", "Key3": "value3"}

        # Act
        result = TestParser.format_key_of_dict(data, str.upper)

        # Assert
        expected = {"KEY1": "value1", "KEY2": "value2", "KEY3": "value3"}
        self.assertEqual(result, expected)

    def test_format_key_of_dict_with_complex_keys_handles_edge_cases(self):
        """Test that format_key_of_dict handles complex key transformations"""
        # Arrange
        data = {
            "APIVersion": "v1",
            "HTTPSProxy": "proxy.example.com",
            "singleword": "value1",
            "Multi_Word_Key": "value2",
        }

        # Act
        result = TestParser.format_key_of_dict(data)

        # Assert
        expected = {
            "api_version": "v1",
            "https_proxy": "proxy.example.com",
            "singleword": "value1",
            "multi_word_key": "value2",
        }
        self.assertEqual(result, expected)

    def test_format_key_of_dict_with_empty_dictionary_returns_empty_dictionary(self):
        """Test that format_key_of_dict handles empty dictionaries"""
        # Arrange
        data = {}

        # Act
        result = TestParser.format_key_of_dict(data)

        # Assert
        self.assertEqual(result, {})

    def test_format_key_of_dict_preserves_value_types_and_content(self):
        """Test that format_key_of_dict preserves all value types and content"""
        # Arrange
        data = {
            "stringKey": "string_value",
            "intKey": 42,
            "floatKey": 3.14,
            "boolKey": True,
            "nullKey": None,
            "listKey": [1, 2, 3],
            "dictKey": {"nested": "value"},
        }

        # Act
        result = TestParser.format_key_of_dict(data)

        # Assert
        self.assertEqual(result["string_key"], "string_value")
        self.assertEqual(result["int_key"], 42)
        self.assertEqual(result["float_key"], 3.14)
        self.assertTrue(result["bool_key"])
        self.assertIsNone(result["null_key"])
        self.assertEqual(result["list_key"], [1, 2, 3])
        self.assertEqual(result["dict_key"], {"nested": "value"})


class TestBaseParserToDictMethod(unittest.TestCase):
    """Test BaseParser.to_dict() method"""

    def test_to_dict_with_simple_parser_returns_dictionary_representation(self):
        """Test that to_dict() returns dictionary representation of simple parser"""
        # Arrange
        parser = TestParser(name="simple_test", value=42)

        # Act
        result = parser.to_dict()

        # Assert
        expected = {
            "name": "simple_test",
            "value": 42,
            "optional_field": None,
            "nested_parser": None,
        }
        self.assertEqual(result, expected)

    def test_to_dict_with_nested_parser_returns_nested_dictionary(self):
        """Test that to_dict() handles nested BaseParser instances"""
        # Arrange
        nested = TestNestedParser(nested_name="nested_test", nested_value=10)
        parser = TestParser(name="with_nested", value=100, nested_parser=nested)

        # Act
        result = parser.to_dict()

        # Assert
        expected = {
            "name": "with_nested",
            "value": 100,
            "optional_field": None,
            "nested_parser": {"nested_name": "nested_test", "nested_value": 10},
        }
        self.assertEqual(result, expected)

    def test_to_dict_with_list_of_parsers_converts_list_elements(self):
        """Test that to_dict() handles lists containing BaseParser instances"""

        # Arrange
        @dataclass
        class ParserWithList(BaseParser):
            items: list[TestNestedParser]
            simple_list: list

        nested1 = TestNestedParser(nested_name="item1", nested_value=1)
        nested2 = TestNestedParser(nested_name="item2", nested_value=2)
        parser = ParserWithList(items=[nested1, nested2], simple_list=["a", "b", "c"])

        # Act
        result = parser.to_dict()

        # Assert
        expected = {
            "items": [
                {"nested_name": "item1", "nested_value": 1},
                {"nested_name": "item2", "nested_value": 2},
            ],
            "simple_list": ["a", "b", "c"],
        }
        self.assertEqual(result, expected)

    def test_to_dict_with_mixed_types_preserves_non_parser_objects(self):
        """Test that to_dict() preserves non-BaseParser objects unchanged"""

        # Arrange
        @dataclass
        class MixedTypesParser(BaseParser):
            string_field: str
            int_field: int
            dict_field: dict
            list_field: list

        parser = MixedTypesParser(
            string_field="test",
            int_field=42,
            dict_field={"key": "value", "nested": {"inner": "data"}},
            list_field=[1, "mixed", {"object": True}, None],
        )

        # Act
        result = parser.to_dict()

        # Assert
        expected = {
            "string_field": "test",
            "int_field": 42,
            "dict_field": {"key": "value", "nested": {"inner": "data"}},
            "list_field": [1, "mixed", {"object": True}, None],
        }
        self.assertEqual(result, expected)


class TestBaseParserPopOptionalFields(unittest.TestCase):
    """Test BaseParser.pop_optional_fields() method"""

    def test_pop_optional_fields_removes_optional_fields_from_data(self):
        """Test that pop_optional_fields removes Optional fields from data"""

        # Arrange
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

        # Act
        parser.pop_optional_fields(data)

        # Assert
        # Optional fields should be removed
        expected = {
            "required_field": "test",
            "regular_field": 42,
            "extra_field": "extra",  # Non-annotated fields remain
        }
        self.assertEqual(data, expected)

    def test_pop_optional_fields_with_complex_union_types_identifies_optional_correctly(
        self,
    ):
        """Test that pop_optional_fields correctly identifies various Union types as optional"""

        # Arrange
        @dataclass
        class ComplexUnionParser(BaseParser):
            required_field: str
            optional_int: Optional[int] = None
            union_str_int: Union[str, int] = ""  # Not optional (no None in Union)
            none_union: Union[None, str] = None  # Optional (None in Union)
            multi_union_with_none: Union[str, int, None] = None  # Optional

        parser = ComplexUnionParser(required_field="test")

        data = {
            "required_field": "test",
            "optional_int": 42,
            "union_str_int": "not_optional",
            "none_union": "should_be_removed",
            "multi_union_with_none": "also_should_be_removed",
        }

        # Act
        parser.pop_optional_fields(data)

        # Assert
        expected = {
            "required_field": "test",
            "union_str_int": "not_optional",  # Union without None stays
        }
        self.assertEqual(data, expected)

    def test_pop_optional_fields_with_no_optional_fields_leaves_data_unchanged(self):
        """Test that pop_optional_fields doesn't modify data when no optional fields exist"""

        # Arrange
        @dataclass
        class NoOptionalParser(BaseParser):
            required_string: str
            required_int: int
            required_bool: bool

        parser = NoOptionalParser(
            required_string="test", required_int=42, required_bool=True
        )

        original_data = {
            "required_string": "test",
            "required_int": 42,
            "required_bool": True,
            "extra_field": "extra",
        }
        data = original_data.copy()

        # Act
        parser.pop_optional_fields(data)

        # Assert
        self.assertEqual(data, original_data)  # Should be unchanged

    def test_pop_optional_fields_with_empty_data_handles_gracefully(self):
        """Test that pop_optional_fields handles empty data dictionary gracefully"""
        # Arrange
        parser = TestParser(name="test", value=42)
        data = {}

        # Act
        parser.pop_optional_fields(data)

        # Assert
        self.assertEqual(data, {})  # Should remain empty


class TestBaseParserEdgeCases(unittest.TestCase):
    """Test BaseParser edge cases and error conditions"""

    def test_base_parser_with_inheritance_preserves_functionality(self):
        """Test that BaseParser functionality works with inheritance"""

        # Arrange
        @dataclass
        class ExtendedParser(TestParser):
            additional_field: str = "default"

        data = {"name": "extended", "value": 999, "additional_field": "custom"}

        # Act
        result = ExtendedParser.parse(data)

        # Assert
        self.assertIsInstance(result, ExtendedParser)
        self.assertEqual(result.name, "extended")
        self.assertEqual(result.value, 999)
        self.assertEqual(result.additional_field, "custom")

    def test_base_parser_format_key_with_identity_function_preserves_keys(self):
        """Test format_key_of_dict with identity function preserves original keys"""
        # Arrange
        data = {"CamelCase": "value1", "snake_case": "value2"}

        # Act
        result = TestParser.format_key_of_dict(data, lambda x: x)  # Identity function

        # Assert
        self.assertEqual(result, data)  # Should be unchanged

    def test_base_parser_to_dict_with_deeply_nested_structures(self):
        """Test to_dict() with deeply nested BaseParser structures"""

        # Arrange
        @dataclass
        class Level3Parser(BaseParser):
            deep_value: str

        @dataclass
        class Level2Parser(BaseParser):
            level3: Level3Parser

        @dataclass
        class Level1Parser(BaseParser):
            level2: Level2Parser

        level3 = Level3Parser(deep_value="deepest")
        level2 = Level2Parser(level3=level3)
        level1 = Level1Parser(level2=level2)

        # Act
        result = level1.to_dict()

        # Assert
        expected = {"level2": {"level3": {"deep_value": "deepest"}}}
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()  # type: ignore
