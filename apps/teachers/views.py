from django.db.models import Count
from rest_framework import generics
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema

from apps.teachers.models import Teacher
from apps.teachers.serializers import (
    TeacherDetailSerializer,
    TeacherListSerializer,
)


@extend_schema(tags=["Teachers"], summary="O'qituvchilar ro'yxati")
class TeacherListAPIView(generics.ListAPIView):
    """Barcha o'qituvchilar va ular bog'liq kurslarining qisqa ro'yxati."""

    permission_classes = [AllowAny]

    queryset = Teacher.objects.prefetch_related(
        "courses"
    ).annotate(
        courses_count=Count("courses")
    )

    serializer_class = TeacherListSerializer


@extend_schema(tags=["Teachers"], summary="O'qituvchi tafsiloti")
class TeacherDetailAPIView(generics.RetrieveAPIView):
    """Slug bo'yicha o'qituvchining to'liq profilini qaytaradi."""

    permission_classes = [AllowAny]

    queryset = Teacher.objects.prefetch_related(
        "courses",
        "courses__teachers",
        "courses__course_type",
    )

    serializer_class = TeacherDetailSerializer
    lookup_field = "slug"