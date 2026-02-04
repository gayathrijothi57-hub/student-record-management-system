from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from pymongo import MongoClient
from bson import ObjectId
from functools import wraps
from datetime import datetime
from django.conf import settings
from .decorators import login_required_mongo,role_required
from .mongo import enrollments_col, courses_col, assignments_col
from django.core.files.storage import FileSystemStorage
from .models import Student, Enrollment, Material
import hashlib

from .mongo import (
    enrollments_col,
    courses_col,
    assignments_col,
    submissions_col
)


# =========================
# MONGODB CONNECTION
# =========================
client = MongoClient("mongodb://localhost:27017/")
db = client["sms_db"]

users_col = db["users"]
courses_col = db["courses"]
enrollments_col = db["enrollments"]
assignments_col = db["assignments"]
materials_col = db["materials"]
notifications_col = db["notifications"]
submissions_col = db["submissions"]

# =========================
# HELPERS
# =========================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# =========================
# AUTH
# =========================
def signup(request):
    if request.method == "POST":
        users_col.insert_one({
            "username": request.POST["username"],
            "email": request.POST["email"],
            "password": hash_password(request.POST["password"]),
            "role": "student"
        })
        messages.success(request, "Account created successfully")
        return redirect("core:login")

    return render(request, "core/auth/signup.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = users_col.find_one({
            "username": username,
            "password": hash_password(password)
        })

        if not user:
            messages.error(request, "Invalid username or password")
            return redirect("core:login")

        request.session.flush()
        request.session["username"] = username
        request.session["role"] = user["role"]

        if user["role"] == "staff":
            return redirect("core:staff_dashboard")
        return redirect("core:student_dashboard")

    return render(request, "core/auth/login.html")


def logout_view(request):
    request.session.flush()
    return redirect("core:login")

# =========================
# DASHBOARD ROUTER
# =========================
@login_required_mongo
def dashboard(request):
    if request.session.get("role") == "staff":
        return redirect("core:staff_dashboard")
    return redirect("core:student_dashboard")

# =========================
# STUDENT
# ========================
@login_required_mongo
@role_required(["student"])
def student_dashboard(request):

    username = request.session.get("username")

    # ✅ Approved courses count
    courses_count = enrollments_col.count_documents({
        "username": username,
        "status": "approved"
    })

    # ✅ Approved enrolled courses (future use)
    enrolled_courses = list(enrollments_col.find(
        {
            "username": username,
            "status": "approved"
        },
        {"course_id": 1, "_id": 0}
    ))

    context = {
        "courses_count": courses_count,
        "enrolled_courses": enrolled_courses,
        "profile_count": 1   # ✅ ADD THIS LINE
    }

    return render(
        request,
        "core/student/dashboard.html",
        context
    )



@login_required_mongo
@role_required(["student"])
def enroll_course(request):
    username = request.session["username"]

    if request.method == "POST":
        enrollments_col.insert_one({
            "username": username,
            "course_id": ObjectId(request.POST["course_id"]),
            "status": "pending",
            "created_at": datetime.now()
        })
        messages.success(request, "Enrollment request sent")
        return redirect("core:student_dashboard")

    courses = list(courses_col.find())
    for c in courses:
        c["id"] = str(c["_id"])

    return render(
        request,
        "core/student/enroll_course.html",
        {"courses": courses}
    )


@login_required_mongo
@role_required(["student"])
def student_profile(request):
    username = request.session["username"]
    user = users_col.find_one({"username": username})

    enrollments = enrollments_col.find({
        "username": username,
        "status": "approved"
    })

    courses = []
    for e in enrollments:
        course = courses_col.find_one({"_id": ObjectId(e["course_id"])})
        if course:
            courses.append(course)

    return render(
        request,
        "core/student/profile.html",
        {
            "user": user,
            "courses": courses
        }
    )


@login_required_mongo
@role_required(["student"])
def edit_student_profile(request):
    username = request.session["username"]
    user = users_col.find_one({"username": username})

    if request.method == "POST":
        users_col.update_one(
            {"username": username},
            {"$set": {"email": request.POST.get("email")}}
        )
        return redirect("core:student_profile")

    return render(
        request,
        "core/student/edit_profile.html",
        {"user": user}
    )

@login_required_mongo
@role_required(["student"])
def student_courses(request):
    username = request.session["username"]

    enrollments = enrollments_col.find({
        "username": username,
        "status": "approved"   # 🔑 only approved
    })

    courses = []

    for e in enrollments:
        course_id = e["course_id"]  # already ObjectId

        course = courses_col.find_one({"_id": course_id})
        if course:
            # 🔑 attach enrollment status
            course["status"] = e["status"]
            courses.append(course)

    return render(
        request,
        "core/student/student_courses.html",
        {"courses": courses}
    )

@login_required_mongo
@role_required(["student"])
def student_materials(request):

    username = request.session.get("username")

    # 1️⃣ Get approved enrollments
    enrollments = enrollments_col.find({
        "username": username,
        "status": "approved"
    })

    course_ids = [e["course_id"] for e in enrollments]

    # 2️⃣ Get materials for those courses
    materials = materials_col.find({
        "course_id": {"$in": course_ids}
    })

    material_list = []

    for m in materials:
        course = courses_col.find_one({"_id": m["course_id"]})

        file_url = None
        if m.get("file"):
            file_url = settings.MEDIA_URL + "materials/" + m["file"]

        material_list.append({
            "title": m.get("title"),
            "course_name": course.get("name") if course else "",
            "file_url": file_url
        })

    return render(
        request,
        "core/student/materials.html",
        {"materials": material_list}
    )


from django.http import FileResponse, Http404
import os

@login_required_mongo
@role_required(["student"])
def download_material(request, filename):

    file_path = os.path.join(
        settings.MEDIA_ROOT,
        "materials",
        filename
    )

    if not os.path.exists(file_path):
        raise Http404("File not found")

    return FileResponse(
        open(file_path, "rb"),
        as_attachment=True,
        filename=filename
    )


# =========================
# STAFF
# =========================
@login_required_mongo
@role_required(["staff"])
def staff_dashboard(request):

    # 🔹 Pending enrollments (table use)
    pending_enrollments = []
    for e in enrollments_col.find({"status": "pending"}):
        course = courses_col.find_one({"_id": e.get("course_id")})

        pending_enrollments.append({
            "id": str(e["_id"]),
            "username": e.get("username"),
            "course_name": course.get("name") if course else "N/A",
        })

    # 🔹 Dashboard COUNTS
    pending_enrollments_count = enrollments_col.count_documents({"status": "pending"})
    approved_enrollments_count = enrollments_col.count_documents({"status": "approved"})
    rejected_enrollments_count = enrollments_col.count_documents({"status": "rejected"})

    
    # ✅ 🔥 ADD THIS LINE (IMPORTANT)
    material_count = materials_col.count_documents({})

    context = {
        "pending_enrollments": pending_enrollments,

        "pending_enrollments_count": pending_enrollments_count,
        "approved_enrollments_count": approved_enrollments_count,
        "rejected_enrollments_count": rejected_enrollments_count,

        
        # 🔥 send to template
        "material_count": material_count,

        "staff_role": "Staff",
        "system_status": "Active",
    }

    return render(request, "core/staff/dashboard.html", context)

# =========================
# MANAGE ENROLLMENTS (PENDING)
# =========================
@login_required_mongo
@role_required(["staff"])
def manage_enrollments(request):

    enrollments = []

    for e in enrollments_col.find({"status": "pending"}):
        course = courses_col.find_one({"_id": e.get("course_id")})

        enrollments.append({
            "id": str(e["_id"]),
            "student": e.get("username"),          # 🔥
            "course": course.get("name") if course else "N/A",
            "status": e.get("status")
        })

    return render(
        request,
        "core/staff/manage_enrollments.html",
        {"enrollments": enrollments}
    )

# =========================
# APPROVE ENROLLMENT
# =========================
@login_required_mongo
@role_required(["staff"])
def approve_enrollment(request, enrollment_id):
    enrollments_col.update_one(
        {"_id": ObjectId(enrollment_id)},
        {"$set": {"status": "approved"}}
    )
    return redirect("core:manage_enrollments")


# =========================
# APPROVED ENROLLMENTS LIST
# ========================

@login_required_mongo
@role_required(["staff"])
def approved_enrollments(request):

    data = []

    enrollments = enrollments_col.find({"status": "approved"})

    for e in enrollments:
        course_id = e.get("course_id")

        course = courses_col.find_one({
            "_id": ObjectId(course_id)
        })

        data.append({
            "username": e.get("username"),
            "course": course.get("name") if course else "N/A",
            "status": e.get("status")
        })

    return render(
        request,
        "core/staff/approved_enrollments.html",
        {"enrollments": data}
    )

# =========================
# REJECTED ENROLLMENTS LIST
# =========================
@login_required_mongo
@role_required(["staff"])
def rejected_enrollments(request):

    data = []

    for e in enrollments_col.find({"status": "rejected"}):
        course = courses_col.find_one({"_id": e.get("course_id")})

        data.append({
            "id": str(e["_id"]),                 # ✅ id safe
            "student_name": e.get("username"),   # ✅ TEMPLATE MATCH
            "course_name": course.get("name") if course else "N/A",
            "status": e.get("status")             # optional
        })

    return render(
        request,
        "core/staff/rejected_enrollments.html",
        {"enrollments": data}
    )


@login_required_mongo
@role_required(["staff"])
def reject_enrollment(request, enrollment_id):

    enrollments_col.update_one(
        {"_id": ObjectId(enrollment_id)},
        {"$set": {"status": "rejected"}}
    )

    return redirect("core:manage_enrollments")

@login_required_mongo
@role_required(["staff"])
def upload_material(request):

    courses = list(courses_col.find())
    for c in courses:
        c["id"] = str(c["_id"])

    if request.method == "POST":

        file = request.FILES.get("file")
        file_name = None

        if file:
            fs = FileSystemStorage(
                location=settings.MEDIA_ROOT / "materials"
            )
            file_name = fs.save(file.name, file)

        materials_col.insert_one({
            "title": request.POST["title"],
            "course_id": ObjectId(request.POST["course_id"]),
            "file": file_name,
            "uploaded_at": datetime.now()
        })

        return redirect("core:staff_dashboard")

    return render(
        request,
        "core/staff/upload_material.html",
        {"courses": courses}
    )
