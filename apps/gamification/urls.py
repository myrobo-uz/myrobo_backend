from django.urls import path

from .views import (
    LeaderboardView,
    MyCertificatesListView,
    MyXPView,
    ProfileStatsView,
    RankListAPIView,
)

urlpatterns = [
    path("ranks/", RankListAPIView.as_view(), name="rank-list"),
    path("my-xp/", MyXPView.as_view(), name="my-xp"),
    path("my-certificates/", MyCertificatesListView.as_view(), name="my-certificates"),
    path("profile-stats/", ProfileStatsView.as_view(), name="profile-stats"),
    path("leaderboard/", LeaderboardView.as_view(), name="leaderboard"),
]
