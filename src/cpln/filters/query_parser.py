"""Advanced query parser for complex container filtering expressions.

This module provides parsing capabilities for complex query syntax like:
- "image:nginx* AND cpu>50"
- "status:healthy OR (memory>80 AND replicas<5)"
- "created_after:2024-01-01 AND name:web-*"
"""

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Union

from .container import ContainerFilterOptions


@dataclass
class QueryToken:
    """Represents a parsed token from a query string."""

    type: str  # 'field', 'operator', 'value', 'logical', 'paren'
    value: str
    position: int


@dataclass
class QueryExpression:
    """Represents a parsed query expression."""

    field: str
    operator: str
    value: Union[str, float, int, datetime]
    negate: bool = False


@dataclass
class LogicalExpression:
    """Represents a logical combination of expressions."""

    operator: str  # 'AND' or 'OR'
    left: Union["LogicalExpression", QueryExpression]
    right: Union["LogicalExpression", QueryExpression]


class QueryParseError(Exception):
    """Raised when query parsing fails."""

    pass


class AdvancedQueryParser:
    """Parser for advanced container filtering query syntax.

    Supports:
    - Field-based filtering: image:nginx*, name:web-*, status:healthy
    - Comparison operators: >, <, >=, <=, =, !=
    - Logical operators: AND, OR, NOT
    - Parentheses for grouping: (status:healthy OR status:degraded) AND cpu>50
    - Time-based queries: created_after:2024-01-01, updated_within:7d
    - Numeric comparisons: cpu>50, memory<=80, replicas>=3
    """

    # Supported fields and their types
    FIELD_TYPES = {
        "name": str,
        "image": str,
        "status": str,
        "health": str,
        "cpu": float,
        "memory": float,
        "replicas": int,
        "replica_utilization": float,
        "created_after": datetime,
        "created_before": datetime,
        "updated_after": datetime,
        "updated_before": datetime,
        "updated_within": timedelta,
        "port": int,
        "env": str,  # Special handling for environment variables
    }

    # Supported operators
    OPERATORS = [">=", "<=", "!=", ">", "<", "=", ":", "~"]

    # Logical operators
    LOGICAL_OPERATORS = ["AND", "OR", "NOT"]

    def __init__(self):
        self.tokens: list[QueryToken] = []
        self.position = 0

    def parse(self, query: str) -> Union[LogicalExpression, QueryExpression]:
        """Parse a query string into a structured expression tree.

        Args:
            query: The query string to parse

        Returns:
            A LogicalExpression or QueryExpression representing the parsed query

        Raises:
            QueryParseError: If the query syntax is invalid
        """
        if not query or not query.strip():
            raise QueryParseError("Empty query string")

        self.tokens = self._tokenize(query)
        self.position = 0

        if not self.tokens:
            raise QueryParseError("No valid tokens found in query")

        result = self._parse_logical_expression()

        if self.position < len(self.tokens):
            remaining = [t.value for t in self.tokens[self.position :]]
            raise QueryParseError(
                f"Unexpected tokens at end of query: {' '.join(remaining)}"
            )

        return result

    def _tokenize(self, query: str) -> list[QueryToken]:
        """Tokenize the query string into meaningful components."""
        tokens = []
        pos = 0

        # Regex patterns for different token types
        patterns = [
            (r"\s+", None),  # Whitespace (skip)
            (r"\(", "paren"),
            (r"\)", "paren"),
            (r"\bAND\b", "logical"),
            (r"\bOR\b", "logical"),
            (r"\bNOT\b", "logical"),
            (r">=|<=|!=|[><=:~]", "operator"),
            (r"[a-zA-Z_][a-zA-Z0-9_]*", "field"),
            (r'"[^"]*"', "quoted_value"),
            (r"'[^']*'", "quoted_value"),
            (r"\d+\.\d+", "float_value"),
            (r"\d+[dhms]", "duration_value"),
            (r"\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2})?", "datetime_value"),
            (r"\d+", "int_value"),
            (r"[^\s()]+", "value"),
        ]

        while pos < len(query):
            matched = False
            for pattern, token_type in patterns:
                regex = re.compile(pattern, re.IGNORECASE)
                match = regex.match(query, pos)
                if match:
                    if token_type:  # Skip whitespace
                        value = match.group()
                        tokens.append(QueryToken(token_type, value, pos))
                    pos = match.end()
                    matched = True
                    break

            if not matched:
                raise QueryParseError(
                    f"Invalid character at position {pos}: '{query[pos]}'"
                )

        return tokens

    def _parse_logical_expression(self) -> Union[LogicalExpression, QueryExpression]:
        """Parse a logical expression (handles AND/OR)."""
        left = self._parse_primary_expression()

        while self.position < len(self.tokens):
            token = self.tokens[self.position]
            if token.type == "logical" and token.value.upper() in ["AND", "OR"]:
                operator = token.value.upper()
                self.position += 1
                right = self._parse_primary_expression()
                left = LogicalExpression(operator, left, right)
            else:
                break

        return left

    def _parse_primary_expression(self) -> Union[LogicalExpression, QueryExpression]:
        """Parse a primary expression (field:value, parentheses, NOT)."""
        if self.position >= len(self.tokens):
            raise QueryParseError("Unexpected end of query")

        token = self.tokens[self.position]

        # Handle NOT operator
        if token.type == "logical" and token.value.upper() == "NOT":
            self.position += 1
            expr = self._parse_primary_expression()
            if isinstance(expr, QueryExpression):
                expr.negate = True
                return expr
            else:
                raise QueryParseError(
                    "NOT operator can only be applied to simple expressions"
                )

        # Handle parentheses
        if token.type == "paren" and token.value == "(":
            self.position += 1
            expr = self._parse_logical_expression()
            if (
                self.position >= len(self.tokens)
                or self.tokens[self.position].value != ")"
            ):
                raise QueryParseError("Missing closing parenthesis")
            self.position += 1
            return expr

        # Handle field:value expressions
        if token.type == "field":
            return self._parse_field_expression()

        raise QueryParseError(f"Unexpected token: {token.value}")

    def _parse_field_expression(self) -> QueryExpression:
        """Parse a field-based expression like 'image:nginx*' or 'cpu>50'."""
        if self.position >= len(self.tokens):
            raise QueryParseError("Expected field name")

        field_token = self.tokens[self.position]
        if field_token.type != "field":
            raise QueryParseError(f"Expected field name, got: {field_token.value}")

        field = field_token.value
        self.position += 1

        if self.position >= len(self.tokens):
            raise QueryParseError(f"Expected operator after field '{field}'")

        operator_token = self.tokens[self.position]
        if operator_token.type != "operator":
            raise QueryParseError(f"Expected operator, got: {operator_token.value}")

        operator = operator_token.value
        self.position += 1

        if self.position >= len(self.tokens):
            raise QueryParseError(f"Expected value after '{field}{operator}'")

        value_token = self.tokens[self.position]
        self.position += 1

        # Convert value based on field type
        value = self._convert_value(field, value_token)

        return QueryExpression(field, operator, value)

    def _convert_value(
        self, field: str, token: QueryToken
    ) -> Union[str, float, int, datetime, timedelta]:
        """Convert a token value to the appropriate type for the field."""
        if field not in self.FIELD_TYPES:
            raise QueryParseError(f"Unknown field: {field}")

        expected_type = self.FIELD_TYPES[field]
        value = token.value

        # Remove quotes from quoted values
        if token.type == "quoted_value":
            value = value[1:-1]  # Remove surrounding quotes

        try:
            if expected_type == str:
                return value
            elif expected_type == int:
                return int(value)
            elif expected_type == float:
                return float(value)
            elif expected_type == datetime:
                return self._parse_datetime(value)
            elif expected_type == timedelta:
                return self._parse_duration(value)
            else:
                return value
        except (ValueError, TypeError) as e:
            raise QueryParseError(
                f"Invalid value '{value}' for field '{field}': {e}"
            ) from e

    def _parse_datetime(self, value: str) -> datetime:
        """Parse a datetime string."""
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue

        raise ValueError(f"Unable to parse datetime: {value}")

    def _parse_duration(self, value: str) -> timedelta:
        """Parse a duration string like '7d', '24h', '30m', '60s'."""
        match = re.match(r"^(\d+)([dhms])$", value.lower())
        if not match:
            raise ValueError(f"Invalid duration format: {value}")

        amount, unit = match.groups()
        amount = int(amount)

        if unit == "d":
            return timedelta(days=amount)
        elif unit == "h":
            return timedelta(hours=amount)
        elif unit == "m":
            return timedelta(minutes=amount)
        elif unit == "s":
            return timedelta(seconds=amount)
        else:
            raise ValueError(f"Unknown duration unit: {unit}")


def parse_advanced_query(query: str) -> Union[LogicalExpression, QueryExpression]:
    """Parse an advanced query string.

    Args:
        query: Query string to parse

    Returns:
        Parsed expression tree

    Example:
        >>> expr = parse_advanced_query("image:nginx* AND cpu>50")
        >>> isinstance(expr, LogicalExpression)
        True
    """
    parser = AdvancedQueryParser()
    return parser.parse(query)


def query_to_filter_options(query: str) -> ContainerFilterOptions:
    """Convert a query string to ContainerFilterOptions.

    This is a simplified conversion for basic queries.
    Complex logical expressions may require custom evaluation.

    Args:
        query: Query string to convert

    Returns:
        ContainerFilterOptions instance
    """
    try:
        expr = parse_advanced_query(query)

        # For simple expressions, we can convert directly
        if isinstance(expr, QueryExpression):
            return _expression_to_filter_options(expr)

        # For complex logical expressions, we need more sophisticated handling
        # This is a placeholder - full implementation would require expression evaluation
        msg = "Complex logical expressions not yet supported in direct conversion"
        raise QueryParseError(msg)

    except Exception as e:
        raise QueryParseError(f"Failed to convert query to filter options: {e}") from e


def _expression_to_filter_options(expr: QueryExpression) -> ContainerFilterOptions:
    """Convert a single expression to ContainerFilterOptions."""
    kwargs = {}

    if expr.field == "name":
        kwargs["name_patterns"] = [expr.value]
    elif expr.field == "image":
        kwargs["image_patterns"] = [expr.value]
    elif expr.field in ["status", "health"]:
        kwargs["health_status"] = [expr.value]
    elif expr.field in ["cpu", "memory", "replica_utilization"] and expr.operator in [
        ">",
        ">=",
    ]:
        kwargs["resource_thresholds"] = {expr.field: expr.value}

    return ContainerFilterOptions(**kwargs)
