from rest_framework import serializers

from apps.payment.models import PaymeTransaction


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
