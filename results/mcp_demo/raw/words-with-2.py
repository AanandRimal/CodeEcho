from devtrust.retrieval import _CAMEL


def words(name: str) -> list[str]:
    """Lowercase words of a snake_case / camelCase identifier."""
    return [p.lower() for chunk in name.split("_") for p in _CAMEL.findall(chunk)]


if __name__ == "__main__":
    assert words("parseHTTPResponse_v2") == ["parse", "http", "response", "v", "2"]
    assert words("snake_case_name") == ["snake", "case", "name"]
    assert words("simpleCamelCase") == ["simple", "camel", "case"]
    print("ok")
