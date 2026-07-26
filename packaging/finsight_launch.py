# PyInstaller entry launcher for the native FinSight.app (target-product §23; ADR-001/ADR-008).
# Thin wrapper so the frozen bundle has a single, stable entry that calls the desktop main().
import sys

from finsight.delivery.desktop.app import main

if __name__ == "__main__":
    sys.exit(main())
