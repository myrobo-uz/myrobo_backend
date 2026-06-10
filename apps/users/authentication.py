from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.settings import api_settings

from apps.users.models import User


class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError:
            raise AuthenticationFailed("Token contains no user id")
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise AuthenticationFailed("User not found")
