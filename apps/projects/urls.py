from django.urls import path

from .views import (
    MyProjectsListAPIView,
    ProjectCreateAPIView,
    ProjectDetailAPIView,
    ProjectListAPIView,
)

urlpatterns = [
    path("projects/", ProjectListAPIView.as_view(), name="project-list"),
    path("projects/create/", ProjectCreateAPIView.as_view(), name="project-create"),
    path("projects/my/", MyProjectsListAPIView.as_view(), name="my-projects"),
    path("projects/<slug:slug>/", ProjectDetailAPIView.as_view(), name="project-detail"),
]
