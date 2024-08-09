import os
import pymongo
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection setup
try:
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['spotify_db']
    plays_collection = db['recent_plays']
except pymongo.errors.ConnectionError as e:
    print(f"Could not connect to MongoDB: {e}")

# Insert a test document to ensure the database and collection are created
test_data = {
    "user_id": "test_user",
    "song_id": "test_song",
    "play_time": "2024-08-08T12:00:00Z"
}

#result = plays_collection.insert_one(test_data)
#print(f"Inserted document ID: {result.inserted_id}")
def store_recent_play(song_name, song_id, play_time):
     # Check if the record already exists

    existing_play = plays_collection.find_one({
        "song_name": song_name,
        "song_id": song_id,
        "play_time": play_time
    })
    # If the record does not exist, insert it
    if not existing_play:
        play_data = {
            "song_name": song_name,
            "song_id": song_id,
            "play_time": play_time
        }
        plays_collection.insert_one(play_data)

def get_recent_plays(user_id, timeframe=24):
    from datetime import datetime, timedelta
    time_threshold = datetime.utcnow() - timedelta(hours=timeframe)
    recent_plays = plays_collection.find({
        "user_id": user_id,
        "play_time": {"$gte": time_threshold}
    })
    return list(recent_plays)
