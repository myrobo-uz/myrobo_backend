from django.db.models import Count
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.pagination import StandardPagination
from apps.users.models import User

from .models import Certificate, Rank
from .serializers import (
    CertificateSerializer,
    MyXPSerializer,
    ProfileStatsSerializer,
    RankSerializer,
)
from .utils import get_current_rank, get_leaderboard_position, get_next_rank


@extend_schema(tags=["Gamification"], summary="Rank bosqichlari ro'yxati")
class RankListAPIView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = RankSerializer
    queryset = Rank.objects.all()
    pagination_class = None


@extend_schema(tags=["Gamification"], summary="Mening XP va rankim")
class MyXPView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        rank = get_current_rank(user)
        next_rank = get_next_rank(user)
        data = {
            "xp": user.xp,
            "rank": rank,
            "next_rank": next_rank,
            "xp_to_next_rank": (next_rank.min_xp - user.xp) if next_rank else None,
            "leaderboard_position": get_leaderboard_position(user),
        }
        return Response(MyXPSerializer(data).data)


@extend_schema(tags=["Gamification"], summary="Mening sertifikatlarim")
class MyCertificatesListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CertificateSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        return Certificate.objects.filter(user=self.request.user).select_related("course")


@extend_schema(tags=["Gamification"], summary="Profil statistikasi (loyiha/kurs/sertifikat/XP/reyting)")
class ProfileStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        rank = get_current_rank(user)
        total_certificates = Certificate.objects.filter(user=user).count()

        total_projects = 0
        try:
            from apps.projects.models import Project
            total_projects = Project.objects.filter(user=user).count()
        except ImportError:
            pass

        data = {
            "xp": user.xp,
            "rank": rank,
            "leaderboard_position": get_leaderboard_position(user),
            "total_courses_completed": total_certificates,
            "total_certificates": total_certificates,
            "total_projects": total_projects,
        }
        return Response(ProfileStatsSerializer(data).data)


@extend_schema(
    tags=["Gamification"],
    summary="Reyting jadvali (top foydalanuvchilar)",
    parameters=[OpenApiParameter("limit", int, required=False, description="Default: 50, max: 100")],
)
class LeaderboardView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            limit = min(int(request.query_params.get("limit", 50)), 100)
        except (TypeError, ValueError):
            limit = 50

        users = User.objects.filter(xp__gt=0).order_by("-xp")[:limit]
        data = []
        for position, user in enumerate(users, start=1):
            rank = get_current_rank(user)
            data.append({
                "position": position,
                "user_id": user.id,
                "full_name": user.full_name,
                "xp": user.xp,
                "rank_title": rank.title if rank else None,
            })
        return Response(data)
