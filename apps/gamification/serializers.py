from rest_framework import serializers

from .models import Certificate, Rank, XPLog


class RankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rank
        fields = ["id", "title", "slug", "min_xp", "icon", "order"]
        read_only_fields = ["id", "slug"]


class XPLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    reason_display = serializers.CharField(source="get_reason_display", read_only=True)

    class Meta:
        model = XPLog
        fields = [
            "id", "user", "user_name", "amount", "reason", "reason_display",
            "description", "target_type", "target_id", "created_at",
        ]


class CertificateSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)
    course_slug = serializers.CharField(source="course.slug", read_only=True)
    user_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = Certificate
        fields = [
            "id", "user", "user_name", "course", "course_title", "course_slug",
            "certificate_number", "created_at",
        ]


class MyXPSerializer(serializers.Serializer):
    xp = serializers.IntegerField()
    rank = RankSerializer(allow_null=True)
    next_rank = RankSerializer(allow_null=True)
    xp_to_next_rank = serializers.IntegerField(allow_null=True)
    leaderboard_position = serializers.IntegerField()


class ProfileStatsSerializer(serializers.Serializer):
    xp = serializers.IntegerField()
    rank = RankSerializer(allow_null=True)
    leaderboard_position = serializers.IntegerField()
    total_courses_completed = serializers.IntegerField()
    total_certificates = serializers.IntegerField()
    total_projects = serializers.IntegerField()


class AwardXPRequestSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
