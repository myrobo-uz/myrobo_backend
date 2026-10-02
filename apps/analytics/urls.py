from django.urls import path

from .views import (
    AnalyticsOverviewView,
    ActionsStatsView,
    CourseProgressDetailView,
    CourseProgressOverviewView,
    DonationsListView,
    DonationsStatsView,
    ExitReasonStatsView,
    LoginsStatsView,
    OnlineUsersView,
    PageExitListView,
    PageStatsView,
    RegistrationsStatsView,
    UserActivityListView,
    UserActivityFilterOptionsView,
    UserActivitySummaryView,
)

app_name = "analytics"

urlpatterns = [
    path("overview/", AnalyticsOverviewView.as_view(), name="overview"),
    path("registrations/", RegistrationsStatsView.as_view(), name="registrations"),
    path("logins/", LoginsStatsView.as_view(), name="logins"),
    path("donations/", DonationsStatsView.as_view(), name="donations"),
    path("donations/list/", DonationsListView.as_view(), name="donations-list"),
    path("courses/progress-overview/", CourseProgressOverviewView.as_view(), name="courses-progress-overview"),
    path("courses/<uuid:course_id>/students/", CourseProgressDetailView.as_view(), name="course-students"),
    path("online/", OnlineUsersView.as_view(), name="online"),
    path("activities/", UserActivityListView.as_view(), name="activities"),
    path("activities/filters/", UserActivityFilterOptionsView.as_view(), name="activities-filters"),
    path("actions-stats/", ActionsStatsView.as_view(), name="actions-stats"),
    path("users/<uuid:user_id>/activity-summary/", UserActivitySummaryView.as_view(), name="user-activity-summary"),
    path("page-exits/", PageExitListView.as_view(), name="page-exits"),
    path("pages/stats/", PageStatsView.as_view(), name="pages-stats"),
    path("pages/exit-reasons/", ExitReasonStatsView.as_view(), name="pages-exit-reasons"),
]
