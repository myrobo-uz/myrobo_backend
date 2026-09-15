from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings

from apps.users.models import User


class OTPVerifySerializer(serializers.Serializer):
    telegram_id = serializers.IntegerField()
    code = serializers.CharField(max_length=6)
    device_id = serializers.CharField()


class TelegramDataSerializer(serializers.Serializer):
    telegram_id = serializers.IntegerField()
    full_name = serializers.CharField(max_length=256)
    phone_number = serializers.CharField(max_length=20)
    telegram_username = serializers.CharField(max_length=256, required=False, allow_blank=True)
    avatar = serializers.ImageField(required=False)


class BotGenerateCodeRequestSerializer(serializers.Serializer):
    telegram_id = serializers.IntegerField(help_text="Telegram user ID")
    full_name = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    telegram_username = serializers.CharField(required=False, allow_blank=True)
    avatar_b64 = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    reuse_phone = serializers.BooleanField(required=False, default=False)


class VerifyCodeRequestSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6, help_text="6 xonali OTP kod")


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "telegram_id",
            "full_name",
            "phone_number",
            "telegram_username",
            "balance",
            "avatar",
            "is_blocked",
        ]
        read_only_fields = ["id", "balance", "is_blocked"]


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "telegram_id",
            "full_name",
            "phone_number",
            "telegram_username",
            "balance",
            "avatar",
            "is_blocked",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "telegram_id", "created_at", "updated_at", "balance", "is_blocked", "phone_number"]


class UserResponseSerializer(serializers.Serializer):
    id = serializers.CharField()
    telegram_id = serializers.IntegerField()
    full_name = serializers.CharField()
    phone_number = serializers.CharField()
    telegram_username = serializers.CharField(allow_null=True)
    avatar = serializers.CharField(allow_null=True)
    balance = serializers.CharField()
    is_blocked = serializers.BooleanField()


class LoginResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserResponseSerializer()


class UserTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        refresh = self.token_class(attrs["refresh"])
        user_id = refresh.payload.get(api_settings.USER_ID_CLAIM)

        if not user_id:
            raise AuthenticationFailed("Token contains no user id")

        try:
            User.objects.get(**{api_settings.USER_ID_FIELD: user_id})
        except (User.DoesNotExist, ValueError, TypeError) as exc:
            raise AuthenticationFailed("User not found") from exc

        data = {"access": str(refresh.access_token)}

        if api_settings.ROTATE_REFRESH_TOKENS:
            if api_settings.BLACKLIST_AFTER_ROTATION:
                try:
                    refresh.blacklist()
                except AttributeError:
                    pass

            refresh.set_jti()
            refresh.set_exp()
            refresh.set_iat()
            data["refresh"] = str(refresh)

        return data


class CodeResponseSerializer(serializers.Serializer):
    code = serializers.CharField()


class ExistsResponseSerializer(serializers.Serializer):
    exists = serializers.BooleanField()
