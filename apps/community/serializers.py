from django.db.models import Count
from rest_framework import serializers

from apps.core.models import Tag
from apps.core.pagination import StandardPagination
from apps.core.serializers import TagSerializer

from .models import CommentLike, Topic, TopicComment, TopicLike


class TopicCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    likes_count = serializers.IntegerField(read_only=True, default=0)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = TopicComment
        fields = [
            "id", "topic", "user", "user_name", "text",
            "is_accepted", "likes_count", "is_liked", "created_at",
        ]
        read_only_fields = ["id", "topic", "user", "is_accepted", "created_at"]

    def get_is_liked(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return CommentLike.objects.filter(comment=obj, user=request.user).exists()


class TopicCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TopicComment
        fields = ["text"]

    def validate_text(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Izoh juda qisqa")
        return value


class TopicListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    comments_count = serializers.IntegerField(read_only=True, default=0)
    likes_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Topic
        fields = [
            "id", "title", "slug", "tags", "is_solved", "views",
            "user", "user_name", "comments_count", "likes_count", "created_at",
        ]


class TopicDetailSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    comments = serializers.SerializerMethodField()
    likes_count = serializers.IntegerField(read_only=True, default=0)
    is_liked = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = [
            "id", "title", "slug", "description", "tags", "is_solved", "views",
            "user", "user_name", "comments", "likes_count", "is_liked",
            "is_owner", "created_at",
        ]

    def get_comments(self, obj):
        request = self.context.get("request")
        comments = (
            obj.comments.filter(is_active=True)
            .select_related("user")
            .annotate(likes_count=Count("likes", distinct=True))
            .order_by("created_at")
        )
        paginator = StandardPagination()
        page = paginator.paginate_queryset(comments, request)
        serializer = TopicCommentSerializer(page, many=True, context=self.context)
        return paginator.get_paginated_response(serializer.data).data

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_is_liked(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return TopicLike.objects.filter(topic=obj, user=request.user).exists()

    def get_is_owner(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and obj.user_id == request.user.id)


class TopicWriteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all(), required=False)

    class Meta:
        model = Topic
        fields = ["id", "slug", "title", "description", "tags"]
        read_only_fields = ["id", "slug"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
