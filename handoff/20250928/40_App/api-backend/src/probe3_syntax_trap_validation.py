import sys

def validate_syntax():
    try:
        # Some code that might raise an exception
        pass
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)