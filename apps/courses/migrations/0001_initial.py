import uuid
import apps.courses.models
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CourseType",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("title", models.CharField(max_length=256)),
                ("slug", models.SlugField(blank=True, unique=True)),
            ],
            options={"abstract": False, "ordering": ["-created_at"], "get_latest_by": "created_at"},
        ),
        migrations.CreateModel(
            name="Course",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("title", models.CharField(max_length=256)),
                ("description", models.TextField()),
                ("price", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("image", models.ImageField(upload_to="courses/images")),
                ("slug", models.SlugField(blank=True, unique=True)),
                ("views", models.BigIntegerField(default=0)),
                (
                    "course_type",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="courses",
                        to="courses.coursetype",
                    ),
                ),
            ],
            options={"abstract": False, "ordering": ["-created_at"], "get_latest_by": "created_at"},
        ),
        migrations.CreateModel(
            name="CourseTelegramLink",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("title", models.CharField(max_length=256)),
                ("chat_id", models.BigIntegerField()),
                (
                    "link_type",
                    models.CharField(
                        choices=[("channel", "Kanal"), ("group", "Gruppa")],
                        default="group",
                        max_length=10,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                (
                    "course",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="telegram_links",
                        to="courses.course",
                    ),
                ),
            ],
            options={"abstract": False, "ordering": ["-created_at"], "get_latest_by": "created_at"},
        ),
        migrations.CreateModel(
            name="Module",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("title", models.CharField(max_length=256)),
                ("slug", models.SlugField(blank=True, unique=True)),
                ("order", models.PositiveIntegerField(default=0)),
                (
                    "course",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="modules",
                        to="courses.course",
                    ),
                ),
            ],
            options={"abstract": False, "ordering": ("order", "id"), "get_latest_by": "created_at"},
        ),
        migrations.CreateModel(
            name="Lesson",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                (
                    "lesson_type",
                    models.CharField(
                        choices=[("content", "Content"), ("code", "Code")],
                        max_length=10,
                    ),
                ),
                ("title", models.CharField(max_length=256)),
                ("description", models.TextField(blank=True)),
                ("video_url", models.CharField(blank=True, max_length=500, null=True)),
                ("slug", models.SlugField(blank=True, unique=True)),
                ("order", models.PositiveIntegerField(default=0)),
                (
                    "module",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lessons",
                        to="courses.module",
                    ),
                ),
            ],
            options={"abstract": False, "ordering": ("order", "id"), "get_latest_by": "created_at"},
        ),
        migrations.CreateModel(
            name="LessonProgress",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("is_completed", models.BooleanField(default=False)),
                ("viewed_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "lesson",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="progress",
                        to="courses.lesson",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lesson_progress",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"abstract": False, "ordering": ["-created_at"], "get_latest_by": "created_at"},
        ),
        migrations.CreateModel(
            name="LessonTask",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField()),
                ("statement", models.TextField()),
                ("sample_input", models.FileField(upload_to=apps.courses.models.lesson_sample_input_path)),
                ("sample_output", models.FileField(upload_to=apps.courses.models.lesson_sample_output_path)),
                (
                    "lesson",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tasks",
                        to="courses.lesson",
                    ),
                ),
            ],
            options={"abstract": False, "ordering": ["-created_at"], "get_latest_by": "created_at"},
        ),
        migrations.CreateModel(
            name="TaskTestCase",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("input_data", models.FileField(upload_to=apps.courses.models.testcase_input_upload_path)),
                ("expected_output", models.FileField(upload_to=apps.courses.models.testcase_output_upload_path)),
                ("is_hidden", models.BooleanField(default=False)),
                (
                    "task",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="test_cases",
                        to="courses.lessontask",
                    ),
                ),
            ],
            options={"abstract": False, "ordering": ["-created_at"], "get_latest_by": "created_at"},
        ),
        migrations.CreateModel(
            name="Submission",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("code", models.TextField()),
                ("language", models.CharField(max_length=50)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("accepted", "Accepted"),
                            ("wrong", "Wrong"),
                            ("error", "Error"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("result", models.JSONField(blank=True, null=True)),
                (
                    "task",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="submissions",
                        to="courses.lessontask",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"abstract": False, "ordering": ["-created_at"], "get_latest_by": "created_at"},
        ),
        migrations.CreateModel(
            name="CoursePlan",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("title", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                ("courses", models.ManyToManyField(related_name="subscription_plans", to="courses.course")),
                ("duration_days", models.PositiveIntegerField()),
                ("price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"abstract": False, "ordering": ["-created_at"], "get_latest_by": "created_at"},
        ),
        migrations.CreateModel(
            name="PromoCode",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("code", models.CharField(max_length=50, unique=True)),
                ("discount_percent", models.PositiveIntegerField()),
                ("is_active", models.BooleanField(default=True)),
                ("max_uses", models.PositiveIntegerField(blank=True, null=True)),
                ("used_count", models.PositiveIntegerField(default=0)),
                ("valid_from", models.DateTimeField(blank=True, null=True)),
                ("valid_to", models.DateTimeField(blank=True, null=True)),
            ],
            options={"abstract": False, "ordering": ["-created_at"], "get_latest_by": "created_at"},
        ),
        migrations.CreateModel(
            name="UserSubscription",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("original_price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("final_price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("subscribed_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("is_active", models.BooleanField(default=True)),
                (
                    "plan",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="user_subscriptions",
                        to="courses.courseplan",
                    ),
                ),
                (
                    "promo_code",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="courses.promocode",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subscriptions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"abstract": False, "ordering": ["-subscribed_at"], "get_latest_by": "created_at"},
        ),
        migrations.CreateModel(
            name="UserCoursePurchase",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("original_price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("final_price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("purchased_at", models.DateTimeField(auto_now_add=True)),
                (
                    "course",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="buyers",
                        to="courses.course",
                    ),
                ),
                (
                    "promo_code",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="courses.promocode",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="purchased_courses",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"abstract": False, "ordering": ["-purchased_at"], "get_latest_by": "created_at"},
        ),
        migrations.CreateModel(
            name="CourseSubscription",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("original_price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("final_price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("is_active", models.BooleanField(default=True)),
                (
                    "course",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="courses.course",
                    ),
                ),
                (
                    "plan",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="courses.courseplan",
                    ),
                ),
                (
                    "promo_code",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="courses.promocode",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"abstract": False, "ordering": ["-created_at"], "get_latest_by": "created_at"},
        ),
        migrations.AddConstraint(
            model_name="lessonprogress",
            constraint=models.UniqueConstraint(
                fields=["user", "lesson"], name="unique_user_lesson_progress"
            ),
        ),
        migrations.AddIndex(
            model_name="lessonprogress",
            index=models.Index(fields=["user", "is_completed"], name="courses_les_user_id_2ae661_idx"),
        ),
        migrations.AddIndex(
            model_name="course",
            index=models.Index(fields=["slug"], name="courses_cou_slug_2e551f_idx"),
        ),
        migrations.AddIndex(
            model_name="course",
            index=models.Index(fields=["course_type"], name="courses_cou_course__320d41_idx"),
        ),
        migrations.AddIndex(
            model_name="submission",
            index=models.Index(fields=["user", "status"], name="courses_sub_user_id_4820f6_idx"),
        ),
        migrations.AddIndex(
            model_name="usercoursepurchase",
            index=models.Index(fields=["user", "course"], name="courses_use_user_id_bf17dc_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="usercoursepurchase",
            unique_together={("user", "course")},
        ),
        migrations.AddIndex(
            model_name="usersubscription",
            index=models.Index(fields=["user", "is_active"], name="courses_use_user_id_ca175f_idx"),
        ),
        migrations.AddIndex(
            model_name="usersubscription",
            index=models.Index(fields=["is_active", "expires_at"], name="courses_use_is_acti_5a9107_idx"),
        ),
        migrations.AddIndex(
            model_name="coursesubscription",
            index=models.Index(fields=["user", "course", "is_active"], name="courses_cou_user_id_aab28b_idx"),
        ),
        migrations.AddIndex(
            model_name="coursesubscription",
            index=models.Index(fields=["is_active", "expires_at"], name="courses_cou_is_acti_612136_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="coursetelegramlink",
            unique_together={("course", "chat_id")},
        ),
    ]
