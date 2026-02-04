from pymongo import MongoClient
from django.conf import settings

# MongoDB connection
client = MongoClient(settings.MONGO_URI)

db = client[settings.MONGO_DB_NAME]

# 🔹 Collections
users_col = db["users"]
courses_col = db["courses"]
enrollments_col = db["enrollments"]
assignments_col = db["assignments"]
submissions_col = db["submissions"]
notifications_col = db["notifications"]
