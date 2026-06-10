from django.urls import path
from apps.teachers.views import (
    TeacherListAPIView,
    TeacherDetailAPIView,
)

urlpatterns = [
    path("teachers/",TeacherListAPIView.as_view(),name="teacher-list",),
    path("teachers/<slug:slug>/",TeacherDetailAPIView.as_view(),name="teacher-detail",),
]