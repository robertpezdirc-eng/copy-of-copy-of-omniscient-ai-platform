# Wrapper to expose FastAPI app for Operational Dashboard
from omni_operational_dashboard import OmniOperationalDashboard

dashboard = OmniOperationalDashboard()
app = dashboard.app