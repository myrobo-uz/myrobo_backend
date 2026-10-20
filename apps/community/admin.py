from django.contrib import admin

from .models import CommentLike, Topic, TopicComment, TopicLike


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "is_solved", "is_active", "views", "created_at")
    list_filter = ("is_solved", "is_active", "created_at")
    search_fields = ("title", "description", "user__full_name")
    readonly_fields = ("slug", "views", "created_at", "updated_at")


@admin.register(TopicComment)
class TopicCommentAdmin(admin.ModelAdmin):
    list_display = ("user", "topic", "is_accepted", "is_active", "created_at")
    list_filter = ("is_accepted", "is_active")
    search_fields = ("text", "user__full_name", "topic__title")
    readonly_fields = ("created_at", "updated_at")


admin.site.register(TopicLike)
admin.site.register(CommentLike)
