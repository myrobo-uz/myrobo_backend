import base64

from django.conf import settings
from django.core.files.base import ContentFile
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import OpenApiParameter, extend_schema

from apps.analytics.activity import ActivityType, log_activity
from apps.analytics.models import LoginLog
from apps.analytics.utils import get_client_ip

from .models import User
from .serializers import (
    BotGenerateCodeRequestSerializer,
    CodeResponseSerializer,
    ExistsResponseSerializer,
    LoginResponseSerializer,
    TelegramDataSerializer,
    UserDetailSerializer,
    VerifyCodeRequestSerializer,
)
from .utils import save_otp, verify_otp


def _user_payload(user, request=None):
    avatar = None
    if user.avatar:
        try:
            avatar = request.build_absolute_uri(user.avatar.url) if request else user.avatar.url
        except Exception:
            avatar = None
    return {
        "id": str(user.id),
        "telegram_id": user.telegram_id,
        "full_name": user.full_name,
        "phone_number": user.phone_number,
        "telegram_username": user.telegram_username,
        "avatar": avatar,
        "balance": str(user.balance),
        "is_blocked": user.is_blocked,
    }


@extend_schema(
    tags=["Auth"],
    summary="Telegram user mavjudligini tekshirish",
    parameters=[OpenApiParameter("telegram_id", int, description="Telegram user ID", required=True)],
    responses={200: ExistsResponseSerializer},
)
class CheckUserView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        telegram_id = request.query_params.get("telegram_id")
        if not telegram_id:
            return Response({"exists": False})
        try:
            exists = User.objects.filter(telegram_id=int(telegram_id)).exists()
        except (TypeError, ValueError):
            return Response({"exists": False})
        return Response({"exists": exists})


@extend_schema(
    tags=["Auth"],
    summary="Bot uchun OTP kod yaratish",
    request=BotGenerateCodeRequestSerializer,
    responses={200: CodeResponseSerializer},
)
class BotGenerateCodeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        telegram_id = request.data.get("telegram_id")
        if not telegram_id:
            return Response({"detail": "telegram_id kerak"}, status=400)

        try:
            telegram_id_int = int(telegram_id)
        except (TypeError, ValueError):
            return Response({"detail": "telegram_id noto'g'ri"}, status=400)

        phone_number = request.data.get("phone_number", "").strip()

        if not phone_number:
            existing = User.objects.filter(telegram_id=telegram_id_int).first()
            if existing and existing.phone_number:
                phone_number = existing.phone_number

        if not phone_number:
            return Response({"detail": "phone_number kerak"}, status=400)

        if request.data.get("phone_number", "").strip():
            User.objects.filter(telegram_id=telegram_id_int).update(phone_number=phone_number)

        extra = {
            "full_name": request.data.get("full_name", ""),
            "phone_number": phone_number,
            "telegram_username": request.data.get("telegram_username", ""),
            "avatar_b64": request.data.get("avatar_b64"),
        }
        code = save_otp(str(telegram_id), extra)
        return Response({"code": code})


@extend_schema(
    tags=["Auth"],
    summary="Telegram user ma'lumotlarini saqlash",
    request={"multipart/form-data": TelegramDataSerializer},
)
class SaveTelegramDataView(APIView):
    permission_classes = [AllowAny]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        telegram_id = request.data.get("telegram_id")
        full_name = request.data.get("full_name")
        phone_number = request.data.get("phone_number")
        telegram_username = request.data.get("telegram_username", "")
        avatar = request.FILES.get("avatar")

        if not telegram_id or not full_name or not phone_number:
            return Response(
                {"error": "telegram_id, full_name, and phone_number are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            telegram_id_int = int(telegram_id)
        except (TypeError, ValueError):
            return Response({"error": "Invalid telegram_id"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user, created = User.objects.get_or_create(
                telegram_id=telegram_id_int,
                defaults={
                    "full_name": full_name,
                    "phone_number": phone_number,
                    "telegram_username": telegram_username or "",
                },
            )

            updated = False
            if not created:
                if user.full_name != full_name:
                    user.full_name = full_name
                    updated = True
                if user.phone_number != phone_number:
                    user.phone_number = phone_number
                    updated = True
                if telegram_username and user.telegram_username != telegram_username:
                    user.telegram_username = telegram_username
                    updated = True

            if avatar:
                user.avatar = avatar
                updated = True

            if created or updated:
                user.save()

            return Response(
                {"status": "success", "user_id": str(user.id), "message": "User data saved successfully"},
                status=status.HTTP_201_CREATED,
            )
        except Exception:
            return Response({"error": "Failed to save user data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=["Auth"],
    summary="OTP kodni tekshirish va login",
    request=VerifyCodeRequestSerializer,
    responses={200: LoginResponseSerializer},
)
class VerifyCodeAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response({"error": "code required"}, status=400)

        result = verify_otp(code)
        if result == "invalid":
            return Response({"error": "invalid"}, status=400)

        try:
            telegram_id = int(result["telegram_id"])
        except (KeyError, TypeError, ValueError):
            return Response({"error": "invalid"}, status=400)

        defaults = {
            "full_name": result.get("full_name", ""),
            "phone_number": result.get("phone_number", ""),
            "telegram_username": result.get("telegram_username", ""),
        }
        user, created = User.objects.update_or_create(telegram_id=telegram_id, defaults=defaults)

        avatar_b64 = result.get("avatar_b64")
        if avatar_b64:
            try:
                img_data = base64.b64decode(avatar_b64)
                user.avatar.save("profile.jpg", ContentFile(img_data), save=True)
            except Exception:
                pass

        LoginLog.objects.create(
            user=user,
            ip=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        log_activity(
            user,
            ActivityType.LOGIN,
            request=request,
            description="signup" if created else "login",
        )

        refresh = RefreshToken.for_user(user)
        return Response({
            "status": "signup" if created else "login",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": _user_payload(user, request),
        })


@extend_schema(
    tags=["Auth"],
    summary="Telegram ID bo'yicha userni olish",
    parameters=[OpenApiParameter("telegram_id", int, description="Telegram user ID", required=True)],
    responses={200: UserDetailSerializer},
)
class GetUserDataView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        telegram_id = request.query_params.get("telegram_id")
        if not telegram_id:
            return Response({"error": "telegram_id parameter required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(telegram_id=int(telegram_id))
        except (TypeError, ValueError):
            return Response({"error": "Invalid telegram_id format"}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response(
                {"found": False, "message": "User with this telegram_id not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        payload = _user_payload(user, request)
        payload["created_at"] = user.created_at.isoformat() if getattr(user, "created_at", None) else None
        payload["updated_at"] = user.updated_at.isoformat() if getattr(user, "updated_at", None) else None
        return Response({"found": True, "user": payload}, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Auth"],
    summary="Joriy foydalanuvchi profili",
    responses={200: UserDetailSerializer},
)
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payload = _user_payload(request.user, request)
        payload["created_at"] = (
            request.user.created_at.isoformat() if getattr(request.user, "created_at", None) else None
        )
        return Response(payload)

    def patch(self, request):
        serializer = UserDetailSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_activity(request.user, ActivityType.PROFILE_UPDATE, request=request)
        return Response(serializer.data)


@extend_schema(tags=["Auth"], summary="Bot uchun barcha foydalanuvchilar telegram_id lari")
class AllTelegramIdsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        secret = settings.BOT_API_SECRET
        if not secret or request.headers.get("X-Bot-Secret") != secret:
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        ids = list(
            User.objects.filter(telegram_id__isnull=False).values_list("telegram_id", flat=True)
        )
        return Response({"telegram_ids": ids})
