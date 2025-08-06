# calculator.py

def add(x, y):
    """Add two numbers."""
    return x + y

def subtract(x, y):
    """Subtract second number from first."""
    return x - y

def multiply(x, y):
    """Multiply two numbers."""
    return x * y

def divide(x, y):
    """Divide first number by second.
    Raises:
        ValueError: If the divisor is zero.
    """
    if y == 0:
        raise ValueError("Cannot divide by zero.")
    return x / y