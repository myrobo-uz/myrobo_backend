from django.urls import path

from .views import LessonTestDetailView, SubmitTestView, TestResultDetailView, TestResultListView

urlpatterns = [
    path("lesson/<slug:lesson_slug>/", LessonTestDetailView.as_view(), name="lesson-test-detail"),
    path("lesson/<slug:lesson_slug>/submit/", SubmitTestView.as_view(), name="lesson-test-submit"),
    path("results/", TestResultListView.as_view(), name="test-result-list"),
    path("results/<uuid:result_id>/", TestResultDetailView.as_view(), name="test-result-detail"),
]
