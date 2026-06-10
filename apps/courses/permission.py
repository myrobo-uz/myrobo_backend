from django.utils import timezone
from rest_framework.permissions import BasePermission

from .models import UserCoursePurchase, UserSubscription


class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "is_admin", False)
        )


class IsCourseSubscribed(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if UserCoursePurchase.objects.filter(user=user, course=obj).exists():
            return True

        return UserSubscription.objects.filter(
            user=user,
            is_active=True,
            expires_at__gt=timezone.now(),
            plan__courses=obj,
        ).exists()


class IsLessonAccessible(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        course = obj.module.course

        if UserCoursePurchase.objects.filter(user=user, course=course).exists():
            return True

        return UserSubscription.objects.filter(
            user=user,
            is_active=True,
            expires_at__gt=timezone.now(),
            plan__courses=course,
        ).exists()
