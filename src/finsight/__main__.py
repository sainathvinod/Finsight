# Implements:
#   ADRs: ADR-013 (single-user local desktop). Enables `python -m finsight` as an official launch path.
#
# Product purpose:
#   Top-level launch entry point for the FinSight desktop application, equivalent to the `finsight`
#   console script. Delegates to the desktop composition root; contains no business logic.
from finsight.delivery.desktop.app import main

if __name__ == "__main__":
    main()
