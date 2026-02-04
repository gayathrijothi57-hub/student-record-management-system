from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["sms_db"]

users_col = db["users"]
students_col = db["students"]
courses_col = db["courses"]
enrollments_col = db["enrollments"]
assignments_col = db["assignments"]
submissions_col = db["submissions"]
materials_col = db["materials"]
