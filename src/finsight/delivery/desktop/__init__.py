# FinSight desktop UI (PySide6). Delivery-layer only: it consumes read-only application query
# services via the composition root and renders them. No SQL, repositories, or business rules here.
# Importing this package pulls in PySide6; the deterministic core never imports it.
