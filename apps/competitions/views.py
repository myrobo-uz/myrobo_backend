from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status as http_status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.pagination import StandardPagination

from .models import Competition, CompetitionParticipant, ParticipantStatus
from .serializers import (
    CompetitionDetailSerializer,
    CompetitionListSerializer,
    CompetitionParticipantSerializer,
)


def _base_queryset():
    return Competition.objects.filter(is_published=True).prefetch_related("directions").annotate(
        participants_count=Count("participants", distinct=True)
    ).order_by("-start_date")


@extend_schema(
    tags=["Competitions"],
    summary="Musobaqalar ro'yxati",
    parameters=[
        OpenApiParameter("status", str, required=False, description="active | finished | upcoming"),
        OpenApiParameter("direction", str, required=False, description="Yo'nalish (teg) slug'i bo'yicha filtr"),
    ],
)
class CompetitionListAPIView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CompetitionListSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = _base_queryset()
        now = timezone.now()
        status_param = self.request.query_params.get("status")
        if status_param == "active":
            qs = qs.filter(start_date__lte=now, end_date__gte=now)
        elif status_param == "finished":
            qs = qs.filter(end_date__lt=now)
        elif status_param == "upcoming":
            qs = qs.filter(start_date__gt=now)

        direction = self.request.query_params.get("direction")
        if direction:
            qs = qs.filter(directions__slug=direction)
        return qs.distinct()


@extend_schema(tags=["Competitions"], summary="Musobaqa tafsiloti")
class CompetitionDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        competition = get_object_or_404(_base_queryset(), slug=slug)
        serializer = CompetitionDetailSerializer(competition, context={"request": request})
        return Response(serializer.data)


@extend_schema(tags=["Competitions"], summary="Musobaqaga ro'yxatdan o'tish", request=None)
class CompetitionJoinAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        competition = get_object_or_404(Competition, slug=slug, is_published=True)
        if competition.status != "active":
            return Response(
                {"detail": "Bu musobaqa hozir faol emas."},
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        participant, created = CompetitionParticipant.objects.get_or_create(
            competition=competition, user=request.user,
        )
        if not created:
            return Response(
                {"detail": "Siz allaqachon ro'yxatdan o'tgansiz."},
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            CompetitionParticipantSerializer(participant, context={"request": request}).data,
            status=http_status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Competitions"], summary="Mening musobaqalarim")
class MyCompetitionsListAPIView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CompetitionParticipantSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        return (
            CompetitionParticipant.objects
            .filter(user=self.request.user)
            .select_related("competition")
        )
