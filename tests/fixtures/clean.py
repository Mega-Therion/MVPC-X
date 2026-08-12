import math

def verify_pythagorean():
    """Verify Pythagorean theorem for (3, 4, 5) triple."""
    a, b, c = 3, 4, 5
    assert a**2 + b**2 == c**2, "Pythagorean theorem failed"
    return True

if __name__ == "__main__":
    result = verify_pythagorean()
    print(f"Verification result: {result}")
