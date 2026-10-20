from rest_framework import serializers

from apps.core.models import Tag
from apps.core.serializers import TagSerializer

from .models import Project


class ProjectListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = Project
        fields = [
            "id", "title", "slug", "image", "tags", "status",
            "views", "user", "user_name", "created_at",
        ]


class ProjectDetailSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = Project
        fields = [
            "id", "title", "slug", "description", "image", "tags", "status",
            "simulator_ref", "views", "user", "user_name", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "slug", "views", "user", "created_at", "updated_at"]


class ProjectWriteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all(), required=False)

    class Meta:
        model = Project
        fields = ["id", "title", "description", "image", "tags", "status", "simulator_ref"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
