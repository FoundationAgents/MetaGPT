# test_calculator.py

import pytest
from calculator import add, subtract, multiply, divide

def test_add():
    assert add(1, 2) == 3
    assert add(-1, -1) == -2
    assert add(-1, 1) == 0

def test_subtract():
    assert subtract(10, 5) == 5
    assert subtract(-1, -1) == 0
    assert subtract(-1, 1) == -2

def test_multiply():
    assert multiply(3, 3) == 9
    assert multiply(-1, -1) == 1
    assert multiply(-1, 1) == -1

def test_divide():
    assert divide(10, 2) == 5
    assert divide(-1, -1) == 1
    assert divide(-1, 1) == -1
    with pytest.raises(ValueError):
        divide(10, 0)