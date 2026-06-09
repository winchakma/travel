import asyncio
from pymongo import MongoClient
import os

def check_db():
    mongo_url = "mongodb+srv://winchakma:win123win@cluster0.htlsc44.mongodb.net/elite_gym?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(mongo_url)
    db = client["elite_gym"]
    col = db["notifications"]
    
    print("Total Notifications in DB:", col.count_documents({}))
    
    # Print all notifications
    for note in col.find({}):
        print("Note ID:", note.get("_id"), "| userEmail:", note.get("userEmail"), "| title:", note.get("title"), "| isRead:", note.get("isRead"), "| is_global:", note.get("is_global"))

if __name__ == "__main__":
    check_db()
