from django.core.cache import cache
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.activity import ActivityType, log_activity
from apps.core.pagination import StandardPagination
from apps.gamification.models import XPReason
from apps.gamification.utils import award_xp

from .models import Project, ProjectStatus
from .permission import IsOwnerOrReadOnly
from .serializers import ProjectDetailSerializer, ProjectListSerializer, ProjectWriteSerializer


@extend_schema(
    tags=["Projects"],
    summary="Loyihalar ro'yxati",
    parameters=[
        OpenApiParameter("search", str, required=False, description="Sarlavha/tavsif bo'yicha qidiruv"),
        OpenApiParameter("tag", str, required=False, description="Teg slug'i bo'yicha filtr"),
        OpenApiParameter("status", str, required=False, description="active | completed | archived"),
        OpenApiParameter("user_id", str, required=False, description="Faqat shu foydalanuvchi loyihalari"),
    ],
)
class ProjectListAPIView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProjectListSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = Project.objects.exclude(status=ProjectStatus.ARCHIVED).select_related("user").prefetch_related("tags")
        params = self.request.query_params

        search = params.get("search")
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))
        tag = params.get("tag")
        if tag:
            qs = qs.filter(tags__slug=tag)
        proj_status = params.get("status")
        if proj_status:
            qs = qs.filter(status=proj_status)
        user_id = params.get("user_id")
        if user_id:
            qs = qs.filter(user_id=user_id)
        return qs.distinct()


@extend_schema(tags=["Projects"], summary="Mening loyihalarim")
class MyProjectsListAPIView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectListSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        return Project.objects.filter(user=self.request.user).prefetch_related("tags")


@extend_schema(tags=["Projects"], summary="Yangi loyiha yaratish", request=ProjectWriteSerializer)
class ProjectCreateAPIView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectWriteSerializer


@extend_schema(tags=["Projects"], summary="Loyiha tafsiloti / yangilash / o'chirish")
class ProjectDetailAPIView(APIView):
    permission_classes = [IsOwnerOrReadOnly]

    def get_object(self, slug):
        obj = get_object_or_404(Project, slug=slug)
        self.check_object_permissions(self.request, obj)
        return obj

    def _increment_views(self, project, request):
        identifier = (
            f"user_{request.user.id}" if request.user.is_authenticated
            else f"ip_{request.META.get('REMOTE_ADDR', 'unknown')}"
        )
        cache_key = f"project_view_{project.id}_{identifier}"
        if not cache.get(cache_key):
            Project.objects.filter(pk=project.pk).update(views=project.views + 1)
            cache.set(cache_key, True, timeout=60 * 60 * 24)

    def get(self, request, slug):
        project = self.get_object(slug)
        self._increment_views(project, request)
        if request.user.is_authenticated:
            log_activity(
                request.user, ActivityType.OTHER, request=request,
                description=f"Loyiha ko'rish: {project.title}", target=project,
            )
        return Response(ProjectDetailSerializer(project, context={"request": request}).data)

    def patch(self, request, slug):
        project = self.get_object(slug)
        previous_status = project.status
        serializer = ProjectWriteSerializer(project, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        project = serializer.save()

        if previous_status != ProjectStatus.COMPLETED and project.status == ProjectStatus.COMPLETED:
            award_xp(
                request.user, amount=50, reason=XPReason.PROJECT_COMPLETE,
                description=project.title, target=project,
            )

        return Response(ProjectDetailSerializer(project, context={"request": request}).data)

    def delete(self, request, slug):
        project = self.get_object(slug)
        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
