import os


def looks_like_test_file(filename: str) -> bool:
    """True if a Python file name looks like a test file."""
    name = os.path.basename(filename)
    return name.endswith(".py") and (name.startswith("test_") or name.endswith("_test.py"))


if __name__ == "__main__":
    assert looks_like_test_file("test_foo.py")
    assert looks_like_test_file("foo_test.py")
    assert looks_like_test_file("pkg/tests/test_bar.py")
    assert not looks_like_test_file("foo.py")
    assert not looks_like_test_file("test_foo.txt")
    assert not looks_like_test_file("contest_foo.py")
    print("ok")
