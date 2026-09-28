from django.urls import path

from .views import ActionCreateView, PageExitCreateView

app_name = "analytics_public"

urlpatterns = [
    path("action/", ActionCreateView.as_view(), name="action-create"),
    path("page-exit/", PageExitCreateView.as_view(), name="page-exit-create"),
]
