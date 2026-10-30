from rest_framework import serializers

from apps.core.serializers import TagSerializer
from apps.core.utils import get_avatar_url

from .models import Competition, CompetitionParticipant


class CompetitionListSerializer(serializers.ModelSerializer):
    directions = TagSerializer(many=True, read_only=True)
    status = serializers.CharField(read_only=True)
    participants_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Competition
        fields = [
            "id", "title", "slug", "image", "directions", "status",
            "start_date", "end_date", "xp_reward", "participants_count",
        ]


class CompetitionDetailSerializer(serializers.ModelSerializer):
    directions = TagSerializer(many=True, read_only=True)
    status = serializers.CharField(read_only=True)
    participants_count = serializers.IntegerField(read_only=True, default=0)
    author_name = serializers.CharField(source="author.full_name", read_only=True, default=None)
    author_avatar = serializers.SerializerMethodField()
    is_joined = serializers.SerializerMethodField()

    class Meta:
        model = Competition
        fields = [
            "id", "title", "slug", "description", "requirements", "image",
            "directions", "status", "start_date", "end_date", "xp_reward",
            "participants_count", "author_name", "author_avatar", "is_joined",
        ]

    def get_author_avatar(self, obj):
        return get_avatar_url(obj.author, self.context.get("request"))

    def get_is_joined(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.participants.filter(user=request.user).exists()


class CompetitionParticipantSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    user_avatar = serializers.SerializerMethodField()
    competition_title = serializers.CharField(source="competition.title", read_only=True)

    class Meta:
        model = CompetitionParticipant
        fields = [
            "id", "competition", "competition_title", "user", "user_name", "user_avatar",
            "status", "submission_note", "xp_awarded", "created_at",
        ]
        read_only_fields = ["id", "competition", "user", "xp_awarded", "created_at"]

    def get_user_avatar(self, obj):
        return get_avatar_url(obj.user, self.context.get("request"))
