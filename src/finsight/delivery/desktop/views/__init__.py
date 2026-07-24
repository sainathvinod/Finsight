# Screen composition only. Views arrange components and bind them to the AppController.
from finsight.delivery.desktop.views.reviews_view import ReviewsView
from finsight.delivery.desktop.views.overview_view import OverviewView
from finsight.delivery.desktop.views.findings_view import FindingsView
from finsight.delivery.desktop.views.audit_view import AuditView
from finsight.delivery.desktop.views.workflow_view import WorkflowView
from finsight.delivery.desktop.views.ask_fin_view import AskFinView

__all__ = ["ReviewsView", "OverviewView", "FindingsView", "AuditView", "WorkflowView", "AskFinView"]
