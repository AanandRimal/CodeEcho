import os


def looks_like_test_file(filename: str) -> bool:
    """True if a Python file name looks like a test file."""
    base = os.path.basename(filename)
    return base.endswith(".py") and (base.startswith("test_") or base.endswith("_test.py"))


if __name__ == "__main__":
    assert looks_like_test_file("test_foo.py")
    assert looks_like_test_file("foo_test.py")
    assert not looks_like_test_file("foo.py")
    assert not looks_like_test_file("test_foo.txt")
    print("ok")
