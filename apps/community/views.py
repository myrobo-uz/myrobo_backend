from django.core.cache import cache
from django.db.models import BooleanField, Count, Exists, OuterRef, Q, Value
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.pagination import StandardPagination

from .models import CommentLike, Topic, TopicComment, TopicLike
from .permission import IsOwnerOrReadOnly
from .serializers import (
    TopicCommentCreateSerializer,
    TopicCommentSerializer,
    TopicDetailSerializer,
    TopicListSerializer,
    TopicWriteSerializer,
)


def _base_queryset(user=None):
    qs = Topic.objects.filter(is_active=True).select_related("user").prefetch_related("tags").annotate(
        comments_count=Count("comments", filter=Q(comments__is_active=True), distinct=True),
        likes_count=Count("likes", distinct=True),
    )
    if user is not None and user.is_authenticated:
        qs = qs.annotate(is_liked=Exists(TopicLike.objects.filter(topic=OuterRef("pk"), user=user)))
    else:
        qs = qs.annotate(is_liked=Value(False, output_field=BooleanField()))
    return qs


@extend_schema(
    tags=["Community"],
    summary="Mavzular ro'yxati",
    parameters=[
        OpenApiParameter("search", str, required=False, description="Sarlavha bo'yicha qidiruv"),
        OpenApiParameter("tag", str, required=False, description="Teg slug'i bo'yicha filtr"),
        OpenApiParameter("is_solved", str, required=False, description="true | false"),
        OpenApiParameter("ordering", str, required=False, description="newest (default) | popular"),
    ],
)
class TopicListAPIView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = TopicListSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = _base_queryset(self.request.user)
        params = self.request.query_params

        search = params.get("search")
        if search:
            qs = qs.filter(title__icontains=search)
        tag = params.get("tag")
        if tag:
            qs = qs.filter(tags__slug=tag)
        is_solved = params.get("is_solved")
        if is_solved is not None:
            qs = qs.filter(is_solved=is_solved.lower() == "true")

        if params.get("ordering") == "popular":
            qs = qs.order_by("-likes_count", "-views", "-created_at")
        else:
            qs = qs.order_by("-created_at")
        return qs.distinct()


@extend_schema(tags=["Community"], summary="Mening mavzularim")
class MyTopicsListAPIView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TopicListSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        return _base_queryset(self.request.user).filter(user=self.request.user).order_by("-created_at")


@extend_schema(tags=["Community"], summary="Yangi mavzu yaratish", request=TopicWriteSerializer)
class TopicCreateAPIView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TopicWriteSerializer


@extend_schema(tags=["Community"], summary="Mavzu tafsiloti / tahrirlash")
class TopicDetailAPIView(APIView):
    permission_classes = [IsOwnerOrReadOnly]

    def get_object(self, slug):
        obj = get_object_or_404(_base_queryset(self.request.user), slug=slug)
        self.check_object_permissions(self.request, obj)
        return obj

    def _increment_views(self, topic, request):
        identifier = (
            f"user_{request.user.id}" if request.user.is_authenticated
            else f"ip_{request.META.get('REMOTE_ADDR', 'unknown')}"
        )
        cache_key = f"topic_view_{topic.id}_{identifier}"
        if not cache.get(cache_key):
            Topic.objects.filter(pk=topic.pk).update(views=topic.views + 1)
            cache.set(cache_key, True, timeout=60 * 60 * 24)

    def get(self, request, slug):
        topic = self.get_object(slug)
        self._increment_views(topic, request)
        return Response(TopicDetailSerializer(topic, context={"request": request}).data)

    def patch(self, request, slug):
        topic = self.get_object(slug)
        serializer = TopicWriteSerializer(topic, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        topic.refresh_from_db()
        return Response(TopicDetailSerializer(topic, context={"request": request}).data)

    def delete(self, request, slug):
        topic = self.get_object(slug)
        topic.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["Community"], summary="Mavzuga izoh qoldirish", request=TopicCommentCreateSerializer)
class TopicCommentCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        topic = get_object_or_404(Topic, slug=slug, is_active=True)
        serializer = TopicCommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = TopicComment.objects.create(
            topic=topic, user=request.user, text=serializer.validated_data["text"],
        )
        return Response(
            TopicCommentSerializer(comment, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Community"], summary="Mavzuni yoqtirish / yoqtirishni bekor qilish", request=None)
class TopicLikeToggleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        topic = get_object_or_404(Topic, slug=slug, is_active=True)
        like, created = TopicLike.objects.get_or_create(topic=topic, user=request.user)
        if not created:
            like.delete()
            return Response({"liked": False})
        return Response({"liked": True})


@extend_schema(tags=["Community"], summary="Izohni yoqtirish / yoqtirishni bekor qilish", request=None)
class CommentLikeToggleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, comment_id):
        comment = get_object_or_404(TopicComment, id=comment_id, is_active=True)
        like, created = CommentLike.objects.get_or_create(comment=comment, user=request.user)
        if not created:
            like.delete()
            return Response({"liked": False})
        return Response({"liked": True})


@extend_schema(
    tags=["Community"],
    summary="Izohni yechim deb belgilash (faqat mavzu egasi)",
    request=None,
)
class CommentAcceptAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, comment_id):
        comment = get_object_or_404(TopicComment, id=comment_id, is_active=True)
        if comment.topic.user_id != request.user.id:
            return Response(
                {"detail": "Faqat mavzu egasi izohni yechim deb belgilashi mumkin."},
                status=status.HTTP_403_FORBIDDEN,
            )
        comment.is_accepted = True
        comment.save(update_fields=["is_accepted", "updated_at"])
        comment.topic.is_solved = True
        comment.topic.save(update_fields=["is_solved", "updated_at"])
        return Response(TopicCommentSerializer(comment, context={"request": request}).data)
