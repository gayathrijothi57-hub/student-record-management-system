from django.urls import path
from . import views

app_name = "core"

urlpatterns = [

    # ---------------- AUTH ----------------
    path("", views.signup, name="signup"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),

    # ---------------- STUDENT ----------------
    path("student/dashboard/", views.student_dashboard, name="student_dashboard"),
    path("student/enroll/", views.enroll_course, name="enroll_course"),
    path("student/profile/", views.student_profile, name="student_profile"),
    path("student/profile/edit/", views.edit_student_profile, name="edit_student_profile"),
    path("student/courses/", views.student_courses, name="student_courses"),
    path(
    "student/materials/",
    views.student_materials,
    name="student_materials"
),
path(
    "student/materials/download/<str:filename>/",
    views.download_material,
    name="download_material"
),

    # ---------------- STAFF ----------------
    path("staff/dashboard/", views.staff_dashboard, name="staff_dashboard"),

    path(
        "staff/manage-enrollments/",
        views.manage_enrollments,
        name="manage_enrollments"
    ),

    # ✅ APPROVE / REJECT ENROLLMENT
    path(
    "staff/enrollment/approve/<str:enrollment_id>/",
    views.approve_enrollment,
    name="approve_enrollment"
),

    path(
    "staff/enrollment/reject/<str:enrollment_id>/",
    views.reject_enrollment,
    name="reject_enrollment"
),


    # ---------------- ENROLLMENT STATUS ----------------
    path(
        "staff/enrollments/approved/",
        views.approved_enrollments,
        name="approved_enrollments"
    ),
    path(
        "staff/enrollments/rejected/",
        views.rejected_enrollments,
        name="rejected_enrollments"
    ),

    # ---------------- MATERIAL ----------------
    path(
        "staff/upload-material/",
        views.upload_material,
        name="upload_material"
    ),
]
