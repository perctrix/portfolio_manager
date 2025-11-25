import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.cache import validate_symbol

def test_path_traversal_protection():
    """Test that path traversal attacks are blocked"""
    print("=" * 60)
    print("Testing Path Traversal Protection")
    print("=" * 60)

    malicious_symbols = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32",
        "AAPL/../../../secret.txt",
        "/etc/passwd",
        "../../data/sensitive.json",
        "AAPL/../../etc/passwd",
        "test/../test2",
        "test\\..\\test2",
    ]

    for symbol in malicious_symbols:
        print(f"\nTesting: {symbol}")
        try:
            validated = validate_symbol(symbol)
            print(f"  FAIL: Symbol was accepted (validated as: {validated})")
        except ValueError as e:
            print(f"  PASS: Blocked with error: {e}")

    print("\n" + "=" * 60)
    print("Testing Valid Symbols")
    print("=" * 60)

    valid_symbols = [
        "AAPL",
        "GOOG",
        "MSFT",
        "^GSPC",
        "^DJI",
        "000001.SS",
        "2330.TW",
        "BRK.B",
        "BRK-B",
    ]

    for symbol in valid_symbols:
        print(f"\nTesting: {symbol}")
        try:
            validated = validate_symbol(symbol)
            print(f"  PASS: Accepted (validated as: {validated})")
        except ValueError as e:
            print(f"  FAIL: Rejected with error: {e}")

    print("\n" + "=" * 60)
    print("Security test completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_path_traversal_protection()
