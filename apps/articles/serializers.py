from rest_framework import serializers

from apps.core.pagination import StandardPagination

from .models import ArticleType, Articles, Comment


class ArticleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleType
        fields = ["id", "title", "slug"]
        read_only_fields = ["title"]


class ArticleSerializer(serializers.ModelSerializer):
    type = serializers.SlugRelatedField(slug_field="title", read_only=True)

    class Meta:
        model = Articles
        fields = ["type", "title", "description", "image", "views", "slug", "created_at"]
        read_only_fields = ["views", "slug", "created_at"]


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.full_name", read_only=True)
    article = serializers.SlugRelatedField(slug_field="slug", queryset=Articles.objects.all())

    class Meta:
        model = Comment
        fields = ["article", "user", "text", "created_at"]
        read_only_fields = ["user", "created_at"]


class ArticleDetailSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source="type.title")
    comments = serializers.SerializerMethodField()

    class Meta:
        model = Articles
        fields = ["type", "title", "description", "image", "views", "slug", "created_at", "comments"]

    def get_comments(self, obj):
        request = self.context.get("request")
        comments = obj.comments.filter(is_active=True).order_by("-created_at")
        paginator = StandardPagination()
        page = paginator.paginate_queryset(comments, request)
        serializer = CommentSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data).data


class CommentCreateSerializer(serializers.ModelSerializer):
    article = serializers.SlugRelatedField(
        slug_field="slug", queryset=Articles.objects.filter(is_active=True)
    )

    class Meta:
        model = Comment
        fields = ["article", "text"]

    def validate_text(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Comment juda qisqa")
        return value

    def create(self, validated_data):
        user = self.context["request"].user
        return Comment.objects.create(user=user, **validated_data)


class ArticleCreateSerializer(serializers.ModelSerializer):
    type_slug = serializers.SlugRelatedField(
        queryset=ArticleType.objects.all(), slug_field="slug", source="type"
    )

    class Meta:
        model = Articles
        fields = ["id", "type_slug", "title", "description", "image"]
