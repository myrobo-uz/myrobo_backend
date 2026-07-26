from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("ckeditor/", include("ckeditor_uploader.urls")),

    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    path("", include("apps.core.urls")),
    path("user/", include("apps.users.urls")),
    path("articles/", include("apps.articles.urls")),
    path("courses/", include("apps.courses.urls")),
    path("teachers/", include("apps.teachers.urls")),
    path("payment/", include("apps.payment.urls")),
    path("lessontest/", include("apps.lessontest.urls")),
    path("api/admin/", include("apps.admin_panel.urls")),
    path("api/admin/analytics/", include("apps.analytics.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
