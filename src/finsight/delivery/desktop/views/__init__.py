# Screen composition only. Views arrange components and bind them to the AppController.
from finsight.delivery.desktop.views.reviews_view import ReviewsView
from finsight.delivery.desktop.views.overview_view import OverviewView
from finsight.delivery.desktop.views.findings_view import FindingsView
from finsight.delivery.desktop.views.audit_view import AuditView
from finsight.delivery.desktop.views.workflow_view import WorkflowView
from finsight.delivery.desktop.views.ask_fin_view import AskFinView
from finsight.delivery.desktop.views.dashboard_view import DashboardView
from finsight.delivery.desktop.views.review_management_view import ReviewManagementView
from finsight.delivery.desktop.views.source_intake_view import SourceIntakeView
from finsight.delivery.desktop.views.financial_review_view import FinancialReviewView
from finsight.delivery.desktop.views.rules_repository_view import RulesRepositoryView
from finsight.delivery.desktop.views.settings_view import SettingsView

__all__ = ["ReviewsView", "OverviewView", "FindingsView", "AuditView", "WorkflowView", "AskFinView",
           "DashboardView", "ReviewManagementView", "SourceIntakeView", "FinancialReviewView",
           "RulesRepositoryView", "SettingsView"]
