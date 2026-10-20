from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AdminDashboardView,
    AdminUserViewSet,
    AdminCourseTypeViewSet,
    AdminCourseViewSet,
    AdminModuleViewSet,
    AdminLessonViewSet,
    AdminLessonTaskViewSet,
    AdminTaskTestCaseViewSet,
    AdminTeacherViewSet,
    AdminArticleTypeViewSet,
    AdminArticleViewSet,
    AdminCommentViewSet,
    AdminCompanyViewSet,
    AdminPromoCodeViewSet,
    AdminCoursePlanViewSet,
    AdminSubscriptionViewSet,
    AdminPurchaseViewSet,
    AdminTransactionViewSet,
    AdminLessonTestViewSet,
    AdminTagViewSet,
    AdminTestQuestionViewSet,
    AdminTestOptionViewSet,
    AdminTestResultViewSet,
    AdminRankViewSet,
    AdminXPLogViewSet,
    AdminCertificateViewSet,
    AdminProjectViewSet,
    AdminCompetitionViewSet,
    AdminCompetitionParticipantViewSet,
    AdminTopicViewSet,
    AdminTopicCommentViewSet,
)

router = DefaultRouter()

# Users
router.register("users", AdminUserViewSet, basename="admin-users")

# Courses
router.register("course-types", AdminCourseTypeViewSet, basename="admin-course-types")
router.register("courses", AdminCourseViewSet, basename="admin-courses")
router.register("modules", AdminModuleViewSet, basename="admin-modules")
router.register("lessons", AdminLessonViewSet, basename="admin-lessons")
router.register("lesson-tasks", AdminLessonTaskViewSet, basename="admin-lesson-tasks")
router.register("test-cases", AdminTaskTestCaseViewSet, basename="admin-test-cases")
router.register("course-plans", AdminCoursePlanViewSet, basename="admin-course-plans")

# Teachers
router.register("teachers", AdminTeacherViewSet, basename="admin-teachers")

# Articles
router.register("article-types", AdminArticleTypeViewSet, basename="admin-article-types")
router.register("articles", AdminArticleViewSet, basename="admin-articles")
router.register("comments", AdminCommentViewSet, basename="admin-comments")

# Tags
router.register("tags", AdminTagViewSet, basename="admin-tags")

# Gamification
router.register("ranks", AdminRankViewSet, basename="admin-ranks")
router.register("xp-logs", AdminXPLogViewSet, basename="admin-xp-logs")
router.register("certificates", AdminCertificateViewSet, basename="admin-certificates")

# Projects
router.register("projects", AdminProjectViewSet, basename="admin-projects")

# Competitions
router.register("competitions", AdminCompetitionViewSet, basename="admin-competitions")
router.register("competition-participants", AdminCompetitionParticipantViewSet, basename="admin-competition-participants")

# Community
router.register("topics", AdminTopicViewSet, basename="admin-topics")
router.register("topic-comments", AdminTopicCommentViewSet, basename="admin-topic-comments")

# Promo
router.register("companies", AdminCompanyViewSet, basename="admin-companies")
router.register("promo-codes", AdminPromoCodeViewSet, basename="admin-promo-codes")

# Sales
router.register("subscriptions", AdminSubscriptionViewSet, basename="admin-subscriptions")
router.register("purchases", AdminPurchaseViewSet, basename="admin-purchases")
router.register("transactions", AdminTransactionViewSet, basename="admin-transactions")

# Lesson Tests
router.register("lesson-tests", AdminLessonTestViewSet, basename="admin-lesson-tests")
router.register("test-questions", AdminTestQuestionViewSet, basename="admin-test-questions")
router.register("test-options", AdminTestOptionViewSet, basename="admin-test-options")
router.register("test-results", AdminTestResultViewSet, basename="admin-test-results")

urlpatterns = [
    path("dashboard/", AdminDashboardView.as_view(), name="admin-dashboard"),
    path("", include(router.urls)),
]
