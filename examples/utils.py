from inflection import camelize, titleize, underscore


def safe_get_attr(obj: object, attr: str, default: str = "N/A") -> str:
    """
    Safely get an attribute from an object, trying different case formats.
    The function will try the following formats in order:
    1. Original attribute name
    2. camelCase
    3. snake_case
    4. TitleCase

    Args:
        obj: The object to get the attribute from
        attr: The name of the attribute to get (in any case format)
        default: The default value to return if the attribute doesn't exist

    Returns:
        The attribute value or the default value

    Examples:
        >>> class Test:
        ...     def __init__(self):
        ...         self.camelCase = "camel"
        ...         self.snake_case = "snake"
        ...         self.TitleCase = "title"
        >>> t = Test()
        >>> safe_get_attr(t, "camel_case")  # Will find camelCase
        'camel'
        >>> safe_get_attr(t, "snakeCase")   # Will find snake_case
        'snake'
        >>> safe_get_attr(t, "title_case")  # Will find TitleCase
        'title'
    """
    # Try different case formats
    formats = [
        attr,  # Original
        camelize(attr, False),  # camelCase
        underscore(attr),  # snake_case
        titleize(attr).replace(" ", ""),  # TitleCase
    ]

    # Try each format
    for fmt in formats:
        try:
            value = getattr(obj, fmt)
            return str(value)
        except AttributeError:
            continue

    return default
