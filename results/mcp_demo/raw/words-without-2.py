import re

_WORD = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|[0-9]+")


def words(name: str) -> list[str]:
    """Lowercase words of a snake_case / camelCase identifier."""
    return [m.group().lower() for m in _WORD.finditer(name)]


if __name__ == "__main__":
    assert words("parseHTTPResponse_v2") == ["parse", "http", "response", "v", "2"]
    assert words("snake_case_name") == ["snake", "case", "name"]
    assert words("getHTTP") == ["get", "http"]
    print("ok")
