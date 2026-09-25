from django.urls import path

from .views import (
    AnalyticsOverviewView,
    CourseProgressDetailView,
    CourseProgressOverviewView,
    DonationsListView,
    DonationsStatsView,
    LoginsStatsView,
    OnlineUsersView,
    RegistrationsStatsView,
    UserActivityListView,
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
    path("users/<uuid:user_id>/activity-summary/", UserActivitySummaryView.as_view(), name="user-activity-summary"),
]
