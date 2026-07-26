from django.urls import path

from .views import (
    PaymeWebhookAPIView,
    PaymeCheckoutLinkAPIView,
    PaymeDonateCheckoutAPIView,
    PaymeTransactionHistoryAPIView,
)

app_name = "payment"

urlpatterns = [
    path("payme/webhook/", PaymeWebhookAPIView.as_view(), name="payme_webhook"),

    path("checkout/", PaymeCheckoutLinkAPIView.as_view(), name="checkout"),
    path("donate/checkout/", PaymeDonateCheckoutAPIView.as_view(), name="donate_checkout"),

    path("history/", PaymeTransactionHistoryAPIView.as_view(), name="history"),
]
