from rest_framework import serializers

from apps.core.models import Tag
from apps.core.serializers import TagSerializer
from apps.core.utils import get_avatar_url

from .models import Project


class ProjectListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    user_avatar = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id", "title", "slug", "image", "tags", "status",
            "views", "user", "user_name", "user_avatar", "created_at",
        ]

    def get_user_avatar(self, obj):
        return get_avatar_url(obj.user, self.context.get("request"))


class ProjectDetailSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    user_avatar = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id", "title", "slug", "description", "image", "tags", "status",
            "simulator_ref", "views", "user", "user_name", "user_avatar", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "slug", "views", "user", "created_at", "updated_at"]

    def get_user_avatar(self, obj):
        return get_avatar_url(obj.user, self.context.get("request"))


class ProjectWriteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all(), required=False)

    class Meta:
        model = Project
        fields = ["id", "slug", "title", "description", "image", "tags", "status", "simulator_ref"]
        read_only_fields = ["id", "slug"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
