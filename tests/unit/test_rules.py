# Verifies: FR-030, FR-033, FR-070 (R-BUD-01/02, R-FND-02)
import unittest
from decimal import Decimal
from finsight.domain.findings import classify_severity, Severity

class TestSeverity(unittest.TestCase):
    def test_bands(self):
        b = {"critical":50,"high":30,"medium":20}
        self.assertEqual(classify_severity(Decimal("30"), b), Severity.HIGH)
        self.assertEqual(classify_severity(Decimal("55"), b), Severity.CRITICAL)
        self.assertEqual(classify_severity(Decimal("20"), b), Severity.MEDIUM)
        self.assertEqual(classify_severity(Decimal("8"), b), Severity.LOW)

if __name__ == "__main__":
    unittest.main()
