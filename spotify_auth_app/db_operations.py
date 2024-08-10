import os
import pymongo
from dotenv import load_dotenv
from datetime import datetime
import pytz

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
    # Convert play_time to a datetime object
    play_time_obj = datetime.fromisoformat(play_time[:-1])  

     # Convert to UTC
    play_time_utc = pytz.utc.localize(play_time_obj)
    
    # Convert UTC to Winnipeg time
    play_time_winnipeg = play_time_utc.astimezone(pytz.timezone('America/Winnipeg'))
    # Separate date and time
    play_date = play_time_winnipeg.date().isoformat()  # YYYY-MM-DD
    play_time_only = play_time_winnipeg.time().isoformat()  # HH:MM:SS.ssssss
     
     # Check if the record already exists
    existing_play = plays_collection.find_one({
        "song_name": song_name,
        "song_id": song_id,
        "play_date": play_date,
        "play_time": play_time_only
    })
    # If the record does not exist, insert it
    if not existing_play:
        play_data = {
            "song_name": song_name,
            "song_id": song_id,
            "play_date": play_date,
            "play_time": play_time_only
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
