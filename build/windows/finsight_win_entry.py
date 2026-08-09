# Implements: F-14-01 — Application Shell (Windows packaged entry point)
#
# PyInstaller entry script for the Windows build. Kept separate from
# finsight/delivery/desktop/__main__.py so the frozen program has a stable, unambiguous
# top-level module name; it adds no behaviour of its own.
from finsight.delivery.desktop.app import main

if __name__ == "__main__":
    main()
