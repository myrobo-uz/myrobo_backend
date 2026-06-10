from django.urls import path
from .views import (
    ArticleTypeListAPIView,
    ArticleListAPIView,
    ArticleDetailAPIView,
    CommentCreateAPIView,
    ArticleCreateView
)

urlpatterns = [
    path("types/", ArticleTypeListAPIView.as_view()),
    path("articles/", ArticleListAPIView.as_view()),
    path("create/", ArticleCreateView.as_view()),
    path("articles/<slug:slug>/", ArticleDetailAPIView.as_view()),
    path("comment-create/", CommentCreateAPIView.as_view()),
]