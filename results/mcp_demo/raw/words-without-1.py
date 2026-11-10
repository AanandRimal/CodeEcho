import re

_SPLIT = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|[0-9]+")


def words(name: str) -> list[str]:
    """Lowercase words of a snake_case or camelCase identifier."""
    return [w.lower() for w in _SPLIT.findall(name)]


if __name__ == "__main__":
    assert words("parseHTTPResponse_v2") == ["parse", "http", "response", "v2"]
    assert words("snake_case_name") == ["snake", "case", "name"]
    assert words("camelCase") == ["camel", "case"]
    assert words("HTTPServer") == ["http", "server"]
