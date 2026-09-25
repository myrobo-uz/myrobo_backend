from rest_framework import serializers

from apps.payment.models import PaymeTransaction

from .models import UserActivity


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
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    user_phone = serializers.CharField(source="user.phone_number", read_only=True)
    action_display = serializers.CharField(source="get_action_display", read_only=True)

    class Meta:
        model = UserActivity
        fields = [
            "id", "user", "user_name", "user_phone", "action", "action_display",
            "description", "target_type", "target_id", "meta", "ip", "created_at",
        ]


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
