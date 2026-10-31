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
            "id", "title", "slug", "image", "tags", "status", "board_type", "is_public",
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
            "simulator_ref", "board_type", "code", "components_json", "wires_json",
            "files", "is_public", "views", "user", "user_name", "user_avatar",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "slug", "views", "user", "created_at", "updated_at"]

    def get_user_avatar(self, obj):
        return get_avatar_url(obj.user, self.context.get("request"))


class ProjectWriteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all(), required=False)

    class Meta:
        model = Project
        fields = [
            "id", "slug", "title", "description", "image", "tags", "status", "simulator_ref",
            "board_type", "code", "components_json", "wires_json", "files", "is_public",
        ]
        read_only_fields = ["id", "slug"]

    def validate_files(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("files ro'yxat (list) bo'lishi kerak.")
        for item in value:
            if not isinstance(item, dict) or "name" not in item or "content" not in item:
                raise serializers.ValidationError(
                    'Har bir fayl {"name": ..., "content": ...} ko\'rinishida bo\'lishi kerak.'
                )
        return value

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
