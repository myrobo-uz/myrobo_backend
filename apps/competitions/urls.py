from django.urls import path

from .views import (
    CompetitionDetailAPIView,
    CompetitionJoinAPIView,
    CompetitionListAPIView,
    MyCompetitionsListAPIView,
)

urlpatterns = [
    path("competitions/", CompetitionListAPIView.as_view(), name="competition-list"),
    path("competitions/my/", MyCompetitionsListAPIView.as_view(), name="my-competitions"),
    path("competitions/<slug:slug>/", CompetitionDetailAPIView.as_view(), name="competition-detail"),
    path("competitions/<slug:slug>/join/", CompetitionJoinAPIView.as_view(), name="competition-join"),
]
