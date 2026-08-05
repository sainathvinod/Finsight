# Reusable UI primitives for the FinSight desktop. Composition only; no business logic or storage.
from finsight.delivery.desktop.components.nav_item import NavItem
from finsight.delivery.desktop.components.section_header import SectionHeader
from finsight.delivery.desktop.components.data_table import DataTable
from finsight.delivery.desktop.components.empty_state import EmptyState
from finsight.delivery.desktop.components.severity import severity_text, severity_color
from finsight.delivery.desktop.components.inspector import DetailInspector
from finsight.delivery.desktop.components.workflow_rail import WorkflowRail
from finsight.delivery.desktop.components.audit_timeline import AuditTimeline, AuditTimelineRow
from finsight.delivery.desktop.components.review_progress import ReviewProgress
from finsight.delivery.desktop.components.appearance_control import (
    AppearanceControl,
    AppearanceMenuButton,
)
from finsight.delivery.desktop.components.inline_message import InlineMessage
from finsight.delivery.desktop.components.confirmation_dialogs import (
    DeleteReviewDialog,
    DialogVariant,
    GovernedSaveDialog,
    InAppDialog,
    InAppMessageDialog,
    InAppTextPromptDialog,
    show_in_app_message,
)
from finsight.delivery.desktop.components.charts import FinancialChartCard
from finsight.delivery.desktop.components.iconography import (
    IconBadge,
    content_icon,
)
from finsight.delivery.desktop.components.adaptive_sidebar import AdaptiveSidebar

__all__ = [
    "NavItem", "SectionHeader", "DataTable", "EmptyState", "severity_text", "severity_color",
    "DetailInspector", "WorkflowRail", "AuditTimeline", "AuditTimelineRow", "ReviewProgress",
    "AppearanceControl", "AppearanceMenuButton",
    "InlineMessage",
    "DialogVariant", "InAppDialog", "InAppMessageDialog", "InAppTextPromptDialog",
    "show_in_app_message",
    "GovernedSaveDialog", "DeleteReviewDialog",
    "FinancialChartCard",
    "IconBadge", "content_icon",
    "AdaptiveSidebar",
]
