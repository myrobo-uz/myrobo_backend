from django.contrib import admin
from .models import ArticleType, Articles, Comment


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ("user", "text", "created_at")
    can_delete = False
    show_change_link = True


@admin.register(ArticleType)
class ArticleTypeAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "created_at")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}  
    ordering = ("-created_at",)


@admin.register(Articles)
class ArticleAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "type",
        "is_active",
        "views",
        "created_at",
    )

    list_filter = ("is_active", "type", "created_at")
    search_fields = ("title", "slug", "description")
    list_editable = ("is_active",)  
    ordering = ("-created_at",)

    readonly_fields = ("views", "slug", "created_at")

    inlines = [CommentInline]  


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "article",
        "user",
        "is_active",
        "created_at",
    )

    list_filter = ("is_active", "created_at")
    search_fields = ("text", "user__id", "article__title")

    list_editable = ("is_active",)  

    ordering = ("-created_at",)