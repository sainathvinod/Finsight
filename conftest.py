# Test bootstrap: make the src/ layout importable so `pytest` resolves the `finsight` package
# without requiring PYTHONPATH=src. (src layout; no editable install needed for the test run.)
import os
import sys

_SRC = os.path.join(os.path.dirname(__file__), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
