import os


def looks_like_test_file(filename: str) -> bool:
    """True if a .py file name looks like a test file."""
    name = os.path.basename(filename)
    return name.endswith(".py") and (
        name.startswith("test_") or name.endswith("_test.py") or name == "conftest.py"
    )


if __name__ == "__main__":
    assert looks_like_test_file("test_foo.py")
    assert looks_like_test_file("foo_test.py")
    assert looks_like_test_file("conftest.py")
    assert not looks_like_test_file("foo.py")
    assert not looks_like_test_file("test_foo.txt")
    print("ok")
