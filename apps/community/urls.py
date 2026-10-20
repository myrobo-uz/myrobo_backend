from django.urls import path

from .views import (
    CommentAcceptAPIView,
    CommentLikeToggleAPIView,
    MyTopicsListAPIView,
    TopicCommentCreateAPIView,
    TopicCreateAPIView,
    TopicDetailAPIView,
    TopicLikeToggleAPIView,
    TopicListAPIView,
)

urlpatterns = [
    path("community/topics/", TopicListAPIView.as_view(), name="topic-list"),
    path("community/topics/create/", TopicCreateAPIView.as_view(), name="topic-create"),
    path("community/topics/my/", MyTopicsListAPIView.as_view(), name="my-topics"),
    path("community/topics/<slug:slug>/", TopicDetailAPIView.as_view(), name="topic-detail"),
    path("community/topics/<slug:slug>/comments/", TopicCommentCreateAPIView.as_view(), name="topic-comment-create"),
    path("community/topics/<slug:slug>/like/", TopicLikeToggleAPIView.as_view(), name="topic-like-toggle"),
    path("community/comments/<uuid:comment_id>/like/", CommentLikeToggleAPIView.as_view(), name="comment-like-toggle"),
    path("community/comments/<uuid:comment_id>/accept/", CommentAcceptAPIView.as_view(), name="comment-accept"),
]
