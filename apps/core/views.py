import logging

from django.conf import settings
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers, status

from apps.courses.telegram_service import send_contact_to_group
from .models import Contact

logger = logging.getLogger(__name__)


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ["name", "email", "message", "image"]

    def validate_message(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Xabar juda qisqa")
        return value


class ContactView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = ContactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contact = serializer.save()

        chat_id = settings.CONTACT_GROUP_CHAT_ID
        if not chat_id:
            logger.warning("CONTACT_GROUP_CHAT_ID sozlanmagan")
        else:
            image_bytes = None
            if contact.image:
                try:
                    contact.image.open()
                    image_bytes = contact.image.read()
                    contact.image.close()
                except Exception as exc:
                    logger.warning("Rasm o'qishda xato: %s", exc)

            send_contact_to_group(
                chat_id=chat_id,
                name=contact.name,
                email=contact.email,
                message=contact.message,
                image_bytes=image_bytes,
            )

        return Response({"status": "ok", "message": "Murojaatingiz qabul qilindi"}, status=status.HTTP_201_CREATED)
