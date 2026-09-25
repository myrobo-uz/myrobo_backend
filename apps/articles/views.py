from django.core.cache import cache
from django.db.models import F
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema

from apps.analytics.activity import ActivityType, log_activity
from apps.core.pagination import StandardPagination

from .models import ArticleType, Articles
from .serializers import (
    ArticleCreateSerializer,
    ArticleDetailSerializer,
    ArticleSerializer,
    ArticleTypeSerializer,
    CommentCreateSerializer,
)


@method_decorator(cache_page(60), name="dispatch")
@extend_schema(tags=["Articles"], summary="Maqola turlari ro'yxati")
class ArticleTypeListAPIView(ListAPIView):
    queryset = ArticleType.objects.all()
    serializer_class = ArticleTypeSerializer
    permission_classes = [AllowAny]


@method_decorator(cache_page(60), name="dispatch")
@extend_schema(tags=["Articles"], summary="Aktiv maqolalar ro'yxati")
class ArticleListAPIView(ListAPIView):
    serializer_class = ArticleSerializer
    pagination_class = StandardPagination
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Articles.objects.filter(is_active=True).select_related("type")
        type_slug = self.request.GET.get("type")
        if type_slug:
            queryset = queryset.filter(type__slug=type_slug)
        return queryset.order_by("-created_at")


@method_decorator(cache_page(60), name="dispatch")
@extend_schema(tags=["Articles"], summary="Maqola tafsiloti")
class ArticleDetailAPIView(RetrieveAPIView):
    queryset = Articles.objects.filter(is_active=True)
    serializer_class = ArticleDetailSerializer
    lookup_field = "slug"
    permission_classes = [AllowAny]

    def _increment_views(self, article, request):
        identifier = (
            f"user_{request.user.id}"
            if request.user.is_authenticated
            else f"ip_{request.META.get('REMOTE_ADDR', 'unknown')}"
        )
        cache_key = f"article_view_{article.id}_{identifier}"
        if not cache.get(cache_key):
            Articles.objects.filter(pk=article.pk).update(views=F("views") + 1)
            cache.set(cache_key, True, timeout=60 * 60 * 24)

    def retrieve(self, request, *args, **kwargs):
        article = self.get_object()
        self._increment_views(article, request)
        if request.user.is_authenticated:
            log_activity(
                request.user, ActivityType.ARTICLE_VIEW, request=request,
                description=article.title, target=article,
            )
        return Response(self.get_serializer(article).data)


@extend_schema(tags=["Articles"], summary="Maqolaga sharh qoldirish")
class CommentCreateAPIView(CreateAPIView):
    serializer_class = CommentCreateSerializer
    permission_classes = [IsAuthenticated]


@extend_schema(tags=["Articles"], summary="Yangi maqola qoralamasi")
class ArticleCreateView(CreateAPIView):
    serializer_class = ArticleCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(is_active=False)
