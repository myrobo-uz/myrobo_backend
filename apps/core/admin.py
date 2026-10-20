from django.contrib import admin
from .models import Contact, Tag


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "created_at")
    search_fields = ("name", "email")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name",)
    readonly_fields = ("slug", "created_at", "updated_at")
