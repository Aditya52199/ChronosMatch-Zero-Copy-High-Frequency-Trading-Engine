import sys


def test_python_version():
    assert sys.version_info >= (3, 11)


def test_required_packages_import():
    import Cython
    import pytest

    assert Cython.__version__
    assert pytest.__version__
