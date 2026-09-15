from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AllTelegramIdsView,
    BotGenerateCodeView,
    CheckUserView,
    GetUserDataView,
    ProfileView,
    SaveTelegramDataView,
    VerifyCodeAPIView,
)
from .serializers import UserTokenRefreshSerializer


class UserTokenRefreshView(TokenRefreshView):
    serializer_class = UserTokenRefreshSerializer

urlpatterns = [
    path("login/", VerifyCodeAPIView.as_view()),
    path("check/", CheckUserView.as_view()),
    path("bot-generate-code/", BotGenerateCodeView.as_view()),
    path("save-telegram-data/", SaveTelegramDataView.as_view()),
    path("get-user-data/", GetUserDataView.as_view()),
    path("profile/", ProfileView.as_view()),
    path("all-telegram-ids/", AllTelegramIdsView.as_view()),
    path("token/refresh/", UserTokenRefreshView.as_view()),
]
