import os
import pymongo
from dotenv import load_dotenv
from datetime import datetime,timedelta
import pytz

# Load environment variables
load_dotenv()

# MongoDB connection setup
try:
    mongo_uri = os.getenv('MONGODB_URI')
    client = pymongo.MongoClient( mongo_uri)
    db = client['spotify_db']
   # plays_collection = db['recent_plays']
except pymongo.errors.ConnectionError as e:
    print(f"Could not connect to MongoDB: {e}")

# Insert a test document to ensure the database and collection are created
test_data = {
    "user_id": "test_user",
    "song_id": "test_song",
    "play_time": "2024-08-08T12:00:00Z"
}


def store_recent_play(song_name, song_id, play_time, user_name,artist_name):
    plays_collection = db[user_name]
    # Convert play_time to a datetime object
    play_time_obj = datetime.fromisoformat(play_time[:-1])  

     # Convert to UTC
    play_time_utc = pytz.utc.localize(play_time_obj)
    # Convert UTC to Winnipeg time
    play_time_winnipeg = play_time_utc.astimezone(pytz.timezone('America/Winnipeg'))
    # Separate date and time
    play_date = play_time_winnipeg  # YYYY-MM-DD
    play_time_only = play_time_winnipeg.time().isoformat()  # HH:MM:SS.ssssss
     
     # Check if the record already exists
    existing_play = plays_collection.find_one({
        "song_name": song_name,
        "song_id": song_id,
        "artist_name": artist_name,
        "play_date": play_date,
        "play_time": play_time_only
    })
    # If the record does not exist, insert it
    if not existing_play:
        play_data = {
            "song_name": song_name,
            "song_id": song_id,
            "artist_name": artist_name,
            "play_date": play_date,
            "play_time": play_time_only
        }
        plays_collection.insert_one(play_data)
       
        print(f"Inserted {song_name} by {artist_name} on {play_date} at {play_time_only} in the database") 

def save_users_to_db(user_id, access_token, refresh_token, token_expiry,email,permissions):
    users_collection = db['users']
    if isinstance(token_expiry, (int, float)):  # Assuming token_expiry is seconds if not datetime
        token_expiry = datetime.utcnow() + timedelta(seconds=token_expiry)


      # Check if the user_id or email already exists
    existing_user = users_collection.find_one({'$or': [{'user_id': user_id}, {'email': email}]})
    
    if existing_user:
        # Update the existing user's details
        users_collection.update_one(
            {'$or': [{'user_id': user_id}, {'email': email}]},
            {
                '$set': {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'token_expiry': token_expiry  
                }
            }
        ,upsert=True  # Ensure that upsert=True is set
        )
        print(f"Updated user with user_id {user_id} or email {email} in the database.")
    else:
        users_collection.insert_one({
            'user_id': user_id,
            'email': email,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_expiry': token_expiry,
            'permissions': permissions

        })
        print(f"Inserted new user with user_id {user_id} and email {email} into the database.")
def get_user_access_token(user_name):
    users_collection = db['users']
    user = users_collection.find_one({'user_id': user_name})
    if user:
        return user['access_token'],user['refresh_token'],user['token_expiry'],user['permissions'],user['email']
    else:
        print(f"User {user_name} not found in the database.")
        return None
def get_user_playlistid(user_name):
    users_collection = db['users']
    user = users_collection.find_one({'user_id': user_name})
    if user:
        return user['playlist_id']
    else:
        print(f"User {user_name} not found in the database.")
        return None
def update_user_permissions(user_name,permissions):
    users_collection = db['users']
    user = users_collection.find_one({'user_id': user_name})
    if user:
        users_collection.update_one(
            {'user_id': user_name},
            {'$set': {'permissions': permissions}}
        )
        print(f"Updated permissions for user {user_name} in the database.")
    else:
        print(f"User {user_name} not found in the database.")
def get_all_users():
    users_collection = db['users']
    all_users = users_collection.find()
    return all_users


def check_for_playlist(user_name, playlist_id):
    """Checks if a playlist with the given ID already exists for the given user."""
    playlist_collection_name = f"{user_name}_playlist"
    playlist_collection = db[playlist_collection_name]

    current_user = db["users"].find_one({"user_id": user_name})
    if current_user and current_user["permissions"].lower().strip() == "yes":
        playlist = playlist_collection.find_one({"playlist_id": playlist_id})
        if playlist:
            print(f"Playlist with ID {playlist_id} already exists for user {user_name}.")
        else:
            update_result = db["users"].update_one(
                {"user_id": user_name},
                {"$set": {"playlist_id": playlist_id}},
            )
            if update_result.matched_count > 0:
                print(f"Updated user {user_name} with playlist ID {playlist_id}.")
            else:
                print(f"No user found with user_id {user_name}.")

from datetime import datetime, timedelta

def get_playlist_tracks(user_name, playlist_id):
    print("Getting playlist tracks for:", user_name)
    print("Starting aggregation process")
    
    plays_collection = db[user_name]
    if plays_collection is None:
        print("Collection not found.")
        raise Exception(f"Collection for user {user_name} does not exist.")
    
    # Calculate the date 10 days ago
    six_days_ago = datetime.now() - timedelta(days=6)
  
    test_query = plays_collection.find({"play_date": {"$gte": six_days_ago}})
   # print(list(test_query))

     # Define the aggregation pipeline
    pipeline = [
        {
            "$match": {  # Match songs where the play_date is greater than 2 days ago
                "play_date": {"$gte": six_days_ago}
            }
        },
        {
            "$group": {  # Group by song name and song_id
                "_id": {
                    "song_name": "$song_name",
                    "song_id": "$song_id"
                },
                "play_count": {"$sum": 1}  # Count occurrences of each song
            }
        },
        {
            "$match": {  # Only include songs that have been played more than 4 times
                "play_count": {"$gte": 4}
            }
        }
       
    ]
    try:
        print("Aggregation pipeline:", pipeline)
        newlist = []
        # Execute the aggregation pipeline
        results = plays_collection.aggregate(pipeline)
         # Check if results are returned
        results_list = list(results)
        if not results_list:
            print("No songs found in the aggregation.")
            return []

       # print("Results found:", results_list)

        # Get the current date
        current_date = datetime.now()
        print("-------------------------------------------------------------------------------------------------------------------------------------------")
        print("Processing song from results\n")

        for song in results_list:
            song_name = song['_id']['song_name']  # Access song name from grouped _id
            song_id = song['_id']['song_id']      # Access song id from grouped _id
            #print(f"Song: {song_name}, ID: {song_id}")
        
            # Add song to playlist (you can uncomment this line when ready)
            send=addsong_to_playlist(user_name, playlist_id, song, current_date)
            print(send)
            if send is True:
                newlist.append(song)
            else:
                print("Song already exists in the playlist")

        print("-------------------------------------------------------------------------------------------------------------------------------------------")

        print("Finished getting playlist tracks for:", user_name)

    except Exception as e:
        # Catch any exceptions and print them
        print(f"Error in get_playlist_tracks: {e}")
        return []


    return newlist
def delete_old_songs(user_name):
    playlist_name = user_name + "_playlist"
    playlist_collection = db[playlist_name]
    newlist = []
    if playlist_collection is None:
        print("Collection not found.")
        raise Exception(f"Collection for user {user_name} does not exist.")
    # Calculate the date 1 month ago
    one_month_ago = datetime.now() - timedelta(days=30)
    print(one_month_ago)
    pipeline = [
        {
            "$match": {  # Match songs where the play_date is greater than 2 days ago
                "Date added": {"$lte": one_month_ago}
            }
        },
        {
            "$group": {  # Group by song name and song_id
                "_id": {
                    "song_name": "$Song_name",
                    "song_id": "$Song_id"
                },
               
            }
        },
    ]
    try:
        print("Aggregation pipeline:", pipeline)
        newlist = []
        # Execute the aggregation pipeline
        results = playlist_collection.aggregate(pipeline)
            # Check if results are returned
        results_list = list(results)
        if not results_list:
            print("No songs found in the aggregation.")
            return []

        # print("Results found:", results_list)

        
        print("-------------------------------------------------------------------------------------------------------------------------------------------")
        print("Processing song from results\n")

        for song in results_list:
            song_name = song['_id']['song_name']  # Access song name from grouped _id
            song_id = song['_id']['song_id']      # Access song id from grouped _id
            newlist.append(song)
        
            playlist_collection.delete_one({'Song_id': song_id})        
            print("Finished removing", song_name, "from the playlist")
   
            

        print("-------------------------------------------------------------------------------------------------------------------------------------------")


    except Exception as e:
        # Catch any exceptions and print them
        print(f"Error in get_playlist_tracks: {e}")
        return []

    return newlist
       
def addsong_to_playlist(user_name,playlist_id,song_details,Date):
    playlist_name = user_name + "_playlist"
    playlist_collection = db[playlist_name]
    song_id=song_details['_id']['song_id']
    song_name=song_details['_id']['song_name']
    update=None
   # print(song_id,song_name)

     # Check if the song already exists
    existing_user = playlist_collection.find_one({'$or': [{'Song_id': song_id}, {'Song_name': {'$regex': song_name, '$options': 'i'}}]})
    
    if existing_user:
        print("song already exists in the playlist")
        print("updating date added")
        store_log_details(user_name, f"{song_name} already exists in the playlist")
        playlist_collection.update_one({'Song_id': song_id}, {"$set": {"Date added": Date}})
        update= False
    else:
        playlist_collection.insert_one({
            'Playlist_id': playlist_id,
            'Song_id': song_id,
            'Song_name': song_name,
            'Date added': Date
            

        })
        print("song added to playlist",playlist_name)
        store_log_details(user_name, f"{song_name} added to the database playlist")
        update= True

    return update
#remove song from playlist
def check_song_from_playlist(user_name,song_id):
    """ Checks if a song with the given song_id already exists in the playlist of the given user.

    Args:
        user_name (str): The name of the user.
        song_id (str): The ID of the song to check.

    Returns:
        bool: True if the song exists in the playlist, False otherwise.
    """
    playlist_name = user_name + "_playlist"
    playlist_collection = db[playlist_name]
    playlist = playlist_collection.find_one({'Song_id': song_id})
    if playlist:
        print(f"Song with ID {song_id} already exists in the playlist.")
        return True
    else:
        print(f"Song with ID {song_id} does not exist in the playlist.")
        return False

def get_all_recent_plays(user_name):
    plays_collection = db[user_name]
    allsongs = plays_collection.find()
    """
    Fetches all recent plays from the database.
    
    Returns:
    - List[dict]: A list of dictionaries containing song information.
    """
    # Query the collection to get all plays, sorted by play_date and play_time
    recent_plays = plays_collection.find().sort(
        [("play_date", pymongo.DESCENDING), ("play_time", pymongo.DESCENDING)]
    )
    # Prepare the output list
    plays_list = []
    
    # Iterate through the results and structure them as required
    for play in recent_plays:
         # Attempt to parse play_date and play_time
        try:
            # Assuming play_date is in 'YYYY-MM-DD' format and play_time in 'HH:MM:SS.ssssss'
            if 'play_date' in play and 'play_time' in play:
                # Parse play_date if it's a string
                if isinstance(play['play_date'], str):
                    date_part = datetime.strptime(play['play_date'], "%Y-%m-%d")
                else:
                    date_part = play['play_date']  # If it's already a datetime object
                time_part = datetime.strptime(play['play_time'].split('.')[0], "%H:%M:%S")  # Ignore milliseconds

                formatted_date = date_part.strftime("%m/%d/%Y")
                formatted_time = time_part.strftime("%I:%M %p")
            else:
                formatted_date = "Unknown Date"
                formatted_time = "Unknown Time"
        except ValueError:
            formatted_date = "Invalid Date"
            formatted_time = "Invalid Time"
        song_details=  f"song_name: {play.get('song_name')} Played_date: {formatted_date},   Played_time: {formatted_time}"
        plays_list.append(song_details)
    
    # Convert the cursor to a list of dictionaries
    return plays_list,allsongs

'''
---------------------------------------------------------------------------------------------------------------------------------------------------

ADmin Login

---------------------------------------------------------------------------------------------------------------------------------------------------
'''
# MongoDB connection setup
try:
    mongo_uri = os.getenv('MONGODB_URI')
    client = pymongo.MongoClient( mongo_uri)
    Admin_db = client['admin_db']
   # plays_collection = db['recent_plays']
except pymongo.errors.ConnectionError as e:
    print(f"Could not connect to MongoDB: {e}")


def get_admin_user(username):
    """Fetches the admin user from the MongoDB collection."""
    try:
            admincollection =  Admin_db["admins"]
            admin_user = admincollection.find_one({"username": username})

            if admin_user:
                print("Admin user found:")
            else:
                print("Admin user not found!")
    except Exception as e:
            print("Error fetching admin user:", e)
    return admin_user

# Store a new admin user
def store_admin_user(admin_data):
    """Stores the admin user in the MongoDB collection."""
    admincollection =  Admin_db["admins"]
    Admin_db.admins.insert_one(admin_data)

def store_log_details(user_name,details):
    """Stores the login details in the MongoDB collection."""
    plays_collection = Admin_db["log_details"]
    Date = datetime.now().strftime("%Y-%m-%d")
    Time = (datetime.now().astimezone(pytz.timezone('America/Winnipeg'))).strftime("%H:%M:%S")
    plays_collection.insert_one({
        'User_name': user_name,
        'Date': Date,
        'Time': Time,
        'Details': details
    })
def get_log_details():
    """Fetches all the login details from the MongoDB collection."""
    plays_collection = Admin_db["log_details"]
    log_details = plays_collection.find()
    return log_details