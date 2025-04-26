from pymongo import MongoClient
import bcrypt
from datetime import datetime

class Database:
    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['youtube_downloader']
        self.users = self.db['users']
        self.downloads = self.db['downloads']

    def register_user(self, username, email, password):
        if self.users.find_one({"username": username}):
            return False, "Username already exists"
        if self.users.find_one({"email": email}):
            return False, "Email already exists"
        
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        self.users.insert_one({
            "username": username,
            "email": email,
            "password": hashed,
            "created_at": datetime.now(),
            "last_login": None
        })
        return True, "Registration successful"

    def login_user(self, username_or_email, password):
        user = self.users.find_one({"$or": [{"username": username_or_email}, {"email": username_or_email}]})
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            self.users.update_one({"_id": user["_id"]}, {"$set": {"last_login": datetime.now()}})
            return True, user["username"]
        return False, "Invalid credentials"

    def save_download(self, username, title, content_type, quality, url, thumbnail_url, format_type, filesize):
        self.downloads.insert_one({
            "username": username,
            "title": title,
            "type": content_type,
            "quality": quality,
            "url": url,
            "timestamp": datetime.now(),
            "thumbnail_url": thumbnail_url,
            "format": format_type,
            "filesize": filesize
        })

    def get_user_downloads(self, username):
        return list(self.downloads.find({"username": username}).sort("timestamp", -1))

    def get_downloads_per_day(self, username):
        pipeline = [
            {"$match": {"username": username}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}},
            {"$limit": 7}
        ]
        result = list(self.downloads.aggregate(pipeline))
        return {item['_id']: item['count'] for item in result}

    def get_content_type_stats(self, username):
        pipeline = [
            {"$match": {"username": username}},
            {"$group": {
                "_id": "$type",
                "count": {"$sum": 1}
            }}
        ]
        result = list(self.downloads.aggregate(pipeline))
        return {item['_id']: item['count'] for item in result} 