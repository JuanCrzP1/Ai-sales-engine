from pydantic import BaseModel


class DashboardMetrics(BaseModel):
    total_clients: int
    cold_leads: int
    warm_leads: int
    hot_leads: int
    total_messages: int
    ai_messages: int
