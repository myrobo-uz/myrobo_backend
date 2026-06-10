from rest_framework import serializers
from apps.teachers.models import Teacher
from apps.courses.serializers import CourseListSerializer

class TeacherListSerializer(serializers.ModelSerializer):
    courses_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Teacher
        fields = [
            "id",
            "first_name",
            "last_name",
            "username",
            "job",
            "image",
            "slug",
            "courses_count",
        ]

class TeacherDetailSerializer(serializers.ModelSerializer):
    courses = CourseListSerializer(many=True, read_only=True)

    class Meta:
        model = Teacher
        fields = [
            "id",
            "first_name",
            "last_name",
            "middle_name",
            "username",
            "job",
            "about",
            "direction",
            "experience",
            "work_place",
            "image",
            "slug",
            "courses",
            "created_at",
        ]


class TeacherShortSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Teacher
        fields = [
            "id",
            "full_name",
            "username",
            "job",
            "image",
            "slug",
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"