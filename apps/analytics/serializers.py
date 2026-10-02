from rest_framework import serializers

from apps.payment.models import PaymeTransaction

from .models import ExitReason, PageExit, UserActivity
from .utils import get_client_ip


class DonationSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    user_telegram_id = serializers.IntegerField(source="user.telegram_id", read_only=True)
    amount_som = serializers.SerializerMethodField()

    class Meta:
        model = PaymeTransaction
        fields = ["id", "user", "user_name", "user_telegram_id", "amount_som", "created_at"]

    def get_amount_som(self, obj):
        return obj.amount_som()


class OnlineUserSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    full_name = serializers.CharField()
    phone_number = serializers.CharField()


class CourseStudentProgressSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    full_name = serializers.CharField()
    phone_number = serializers.CharField()
    completed_lessons = serializers.IntegerField()
    total_lessons = serializers.IntegerField()
    percent = serializers.FloatField()


class CourseProgressOverviewSerializer(serializers.Serializer):
    course_id = serializers.UUIDField()
    course_title = serializers.CharField()
    enrolled_count = serializers.IntegerField()
    total_lessons = serializers.IntegerField()
    avg_completion_percent = serializers.FloatField()


class PeriodCountSerializer(serializers.Serializer):
    period = serializers.DateField()
    count = serializers.IntegerField()


class PeriodDonationSerializer(serializers.Serializer):
    period = serializers.DateField()
    count = serializers.IntegerField()
    total_som = serializers.FloatField()


class UserActivitySerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_phone = serializers.SerializerMethodField()
    action_display = serializers.CharField(source="get_action_display", read_only=True)

    class Meta:
        model = UserActivity
        fields = [
            "id", "user", "user_name", "user_phone", "anonymous_id", "action", "action_display",
            "description", "page", "path", "target_type", "target_id", "meta", "ip", "created_at",
        ]

    def get_user_name(self, obj):
        return obj.user.full_name if obj.user_id else None

    def get_user_phone(self, obj):
        return obj.user.phone_number if obj.user_id else None


class ActivityFilterOptionSerializer(serializers.Serializer):
    value = serializers.CharField()
    label = serializers.CharField()


class UserActivityFilterOptionsSerializer(serializers.Serializer):
    actions = ActivityFilterOptionSerializer(many=True)
    pages = ActivityFilterOptionSerializer(many=True)
    target_types = ActivityFilterOptionSerializer(many=True)


class UserActivitySummarySerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    full_name = serializers.CharField()
    phone_number = serializers.CharField()
    is_online = serializers.BooleanField()
    login_count = serializers.IntegerField()
    last_login = serializers.DateTimeField(allow_null=True)
    last_seen = serializers.DateTimeField(allow_null=True)
    total_activities = serializers.IntegerField()
    action_counts = serializers.DictField(child=serializers.IntegerField())


class ActionCreateSerializer(serializers.Serializer):
    """`POST /api/analytics/action/` uchun kirish validatsiyasi.

    Login qilgan foydalanuvchi `request.user` orqali aniqlanadi; login
    qilmagan foydalanuvchi uchun `anonymous_id` majburiy.
    """

    anonymous_id = serializers.CharField(max_length=64, required=False, allow_blank=True, default="")
    action = serializers.CharField(max_length=30)
    page = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    path = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    description = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    meta = serializers.JSONField(required=False, default=dict)

    def validate_action(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("action bo'sh bo'lishi mumkin emas.")
        return value

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user if request.user.is_authenticated else None
        if not user and not attrs.get("anonymous_id"):
            raise serializers.ValidationError(
                {"anonymous_id": "Login qilmagan foydalanuvchi uchun anonymous_id majburiy."}
            )
        attrs["_user"] = user
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        user = validated_data.pop("_user")
        anonymous_id = validated_data.pop("anonymous_id", "") if not user else ""
        return UserActivity.objects.create(
            user=user,
            anonymous_id=anonymous_id,
            action=validated_data["action"],
            description=validated_data.get("description", ""),
            page=validated_data.get("page", ""),
            path=validated_data.get("path", ""),
            meta=validated_data.get("meta") or {},
            ip=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )


class PageExitSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_phone = serializers.SerializerMethodField()
    exit_reason_display = serializers.CharField(source="get_exit_reason_display", read_only=True)

    class Meta:
        model = PageExit
        fields = [
            "id", "user", "user_name", "user_phone", "anonymous_id",
            "page", "path", "exit_reason", "exit_reason_display",
            "time_spent", "ip", "created_at",
        ]

    def get_user_name(self, obj):
        return obj.user.full_name if obj.user_id else None

    def get_user_phone(self, obj):
        return obj.user.phone_number if obj.user_id else None


class PageExitCreateSerializer(serializers.Serializer):
    """`POST /api/analytics/page-exit/` uchun kirish validatsiyasi."""

    anonymous_id = serializers.CharField(max_length=64, required=False, allow_blank=True, default="")
    page = serializers.CharField(max_length=100)
    path = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    exit_reason = serializers.ChoiceField(choices=ExitReason.choices, required=False, default=ExitReason.UNKNOWN)
    time_spent = serializers.IntegerField(min_value=0, required=False, default=0)

    def validate_page(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("page bo'sh bo'lishi mumkin emas.")
        return value

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user if request.user.is_authenticated else None
        if not user and not attrs.get("anonymous_id"):
            raise serializers.ValidationError(
                {"anonymous_id": "Login qilmagan foydalanuvchi uchun anonymous_id majburiy."}
            )
        attrs["_user"] = user
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        user = validated_data.pop("_user")
        anonymous_id = validated_data.pop("anonymous_id", "") if not user else ""
        return PageExit.objects.create(
            user=user,
            anonymous_id=anonymous_id,
            page=validated_data["page"],
            path=validated_data.get("path", ""),
            exit_reason=validated_data.get("exit_reason", ExitReason.UNKNOWN),
            time_spent=validated_data.get("time_spent", 0),
            ip=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )


class PageStatsSerializer(serializers.Serializer):
    page = serializers.CharField()
    views = serializers.IntegerField()
    exits = serializers.IntegerField()
    avg_time_spent = serializers.FloatField()


class ExitReasonStatsSerializer(serializers.Serializer):
    exit_reason = serializers.CharField()
    count = serializers.IntegerField()
