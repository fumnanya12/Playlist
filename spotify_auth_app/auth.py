from dotenv import load_dotenv
from flask import Flask, flash, redirect, request, session, url_for
import requests
import os
from datetime import datetime,timedelta
from .db_operations import store_recent_play, get_all_recent_plays,save_users_to_db,get_user_access_token,get_all_users,check_for_playlist,get_playlist_tracks,update_user_permissions,get_user_playlistid
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from pytz import timezone
import atexit
from werkzeug.security import generate_password_hash, check_password_hash




# Load environment variables fclearom .env file
load_dotenv()
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize the scheduler
scheduler = BackgroundScheduler()


# Replace these with your own Spotify credentials
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = 'https://testspotify-af120bb16cf3.herokuapp.com/callback'

# Spotify authorization URL
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'


# variable to store user data
user_name = None
user_email = None
global_permissions = None




# Function to start the scheduler if it's not already running
def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        print("Scheduler started.")


def refresh_access_token( user_id):
    user_acess_token,user_refresh_token,token_expiry,user_permission=get_user_access_token(user_id)
    if not user_refresh_token:
        print("No refresh token available.")
        return None

    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': user_refresh_token,
        'client_id': SPOTIPY_CLIENT_ID,
        'client_secret': SPOTIPY_CLIENT_SECRET
    }
    response = requests.post(TOKEN_URL, data=payload)
    if response.status_code == 200:
        refreshed_tokens = response.json()
        access_token = refreshed_tokens.get('access_token')
        expires_in = refreshed_tokens.get('expires_in')
        new_refresh_token = refreshed_tokens.get('refresh_token', user_refresh_token)
        #save_tokens(access_token, new_refresh_token, expires_in)
        save_users_to_db(user_id, access_token, new_refresh_token, expires_in,user_email,global_permissions)
        print("refresh_access_token method")
        print(f"Access token refreshed: {access_token}")
        print(f"Refresh token refreshed: {new_refresh_token}")
        return access_token, new_refresh_token
    else:
        print(f"Failed to refresh access token: {response.status_code}, {response.text}")
        return None
def get_access_token():
    print("get_access_token method: ", user_name)
    user_acess_token,user_refresh_token,token_expiry,user_permission=get_user_access_token(user_name)

  
    if token_expiry is None:
        print("No token available.")
        return None
    if datetime.utcnow() >= token_expiry:
        print("Token expired, refreshing...")
        return refresh_access_token(user_name)
    print(f"Using access token: { user_acess_token}")
    return  user_acess_token


@app.route('/')
def index():
    result= f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">  
        <title>Welcome page</title>
        <link rel="stylesheet" type="text/css" href="{url_for('static', filename='welcome.css')}">

    </head>
    <body>
    
     <div class="container">
            <div class="loader" id="loader"></div>
            <div class="content" id="content">
                <h1>Welcome to the Spotify Stats app!</h1>
                <a href="/login" class="btn">Login with Spotify</a>
            </div>
        <!-- Loader -->
    <script src="{url_for('static', filename='script.js')}"></script>
    
    </body>
    </html>
    '''
    return result

@app.route('/login')
def login():
    # Redirect user to Spotify's authorization page
    auth_query = {
        'response_type': 'code',
        'client_id': SPOTIPY_CLIENT_ID,
        'redirect_uri': SPOTIPY_REDIRECT_URI,
        'scope': 'user-library-read playlist-read-private playlist-read-collaborative user-read-recently-played user-top-read user-read-private user-read-email playlist-modify-public playlist-modify-private'
    }
    auth_url = requests.Request('GET', AUTH_URL, params=auth_query).prepare().url
    return redirect(auth_url)

@app.route('/logout')
def logout():
    global user_name,global_permissions,user_email
    # Clear the session
    session.clear()

    # Optionally, add a logout message
    print('You have been logged out.', 'info')
    print(user_name,"User logged out")

    # Redirect to the login page or home page
    return redirect(url_for('index'))
#removing the methode now the databased  has updated

@app.route('/callback')
def callback():
    global user_name,global_permissions,user_email

    code = request.args.get('code')
    if not code: 
        return 'Authorization failed.'

    # Exchange the authorization code for an access token
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': SPOTIPY_REDIRECT_URI,
        'client_id': SPOTIPY_CLIENT_ID,
        'client_secret': SPOTIPY_CLIENT_SECRET
    }
    token_response = requests.post(TOKEN_URL, data=token_data)
    token_info = token_response.json()
    access_token = token_info.get('access_token')
    refresh_token = token_info.get('refresh_token')
    expires_in = token_info.get('expires_in')
    print(token_info)

    if not access_token:
        print('Failed to retrieve access token.')
        return redirect(url_for('login'))



    # Use the access token to get user profile data
    headers = {'Authorization': f'Bearer {access_token}'}
    profile_response = requests.get('https://api.spotify.com/v1/me', headers=headers)
    profile_data = profile_response.json()
    user_id =None
    # Extract user information
    if(profile_data.get('id') is not profile_data.get('display_name')):
        user_id=profile_data.get('display_name')
    else:
        user_id=profile_data.get('id') # Spotify user ID
    #user_id = profile_data.get('id')  
    email = profile_data.get('email')  # User email
    #print(profile_data)
    permission="no"
    
    user_name=user_id
    
    save_users_to_db(user_id, access_token, refresh_token, expires_in,email,permission)
   
    print("User information retrieved successfully. callback method")
    # Store access token in a global variable
   
 
    
    user_name=user_id


    return redirect(url_for('welcome'))
@app.route('/submit_permission', methods=['POST'])
def submit_permission():
    data = request.json
    update_user_permissions(user_name,data['response'])
    return 
"Welcome Page"
@app.route('/welcome')
def welcome():
    user_acess_token,user_refresh_token,token_expiry,user_permission=get_user_access_token(user_name)
    response=user_permission
    print("Welcome page")
    access_token = get_access_token()
    print(access_token)
    if not access_token:
        return redirect(url_for('login'))
    headers = {'Authorization': f'Bearer {access_token}'}
    profile_r = requests.get('https://api.spotify.com/v1/me', headers=headers)
    profile_json = profile_r.json()
    
    profile_r = requests.get('https://api.spotify.com/v1/me', headers=headers)
    profile_json = profile_r.json()
    current_user_name= profile_json.get("display_name")
    current_user_email= profile_json.get("email")
    current_user_img= profile_json.get("images")
    if current_user_img:
        img_url = current_user_img[1].get("url")
    else:
        img_url = url_for('static', filename='user-solid.svg')
   
    result= f'''
        <!DOCTYPE html>
        <html lang="en" dir="ltr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0"> 
            <title> Welcome page | Spotify activity   </title> 
                <link rel="stylesheet" type="text/css" href="{url_for('static', filename='Profile.css')}">
        </head>
        <body>
            <div class="container">  
            <h1>Hello, {profile_json.get("display_name")}!</h1>
            <a href="/logout">
            <button> <span>Logout</span>
            </button> </a>
            <ul class="nav-links">
                 <li id="openModal" ><a href=#>Profile</a></li>
                <li class="center"><a href="/profile">Playlists</a></li>
                <li class="upward"><a href="/recently_played">Recently played</a></li>
                <li class="forward"><a href="/store_play">Statistics</a></li>
            </ul>
            </div>
        <!-- Modal structure -->
            <div id="myModal" class="modal">
                <div class="modal-content">
                <span class="close">&times;</span>
                <h2>User Profile Information</h2>

                <!-- Profile Information -->
                <div class="profile-info">
                    
                    <div class="icon"> 
                    <img src="{img_url}" alt="Logo">
                    </div>
                    <div class="profile-text">
                    <p><strong>Name:</strong> {current_user_name}</p>
                    <p><strong>Email:</strong> {current_user_email}</p>
                   
                    </div>
                    
                </div>
                <!-- Permission Section -->
                <div class="permission-section">
                    <p>Do you grant permission?</p>
                    <div class="buttons">
                    <button class="yes-button">Yes</button>
                    <button class="no-button">No</button>
                    </div>
                </div>


                </div>
                </div>
         <!-- Hidden element to store the response dynamically from Flask -->
         <div id="permission-response" data-response="{response}" style="display: none;"></div>
            <script src="{ url_for('static', filename='profile.js') }"></script>

       
        </body>
        </html>
    '''

    return result



@app.route('/profile')
def profile():
    print("Profile page")
    access_token = get_access_token()
    print(access_token)

    if not access_token:
        return redirect(url_for('login'))
    # Fetch user profile information
    headers = {'Authorization': f'Bearer {access_token}'}
    profile_r = requests.get('https://api.spotify.com/v1/me', headers=headers)
    profile_json = profile_r.json()
    # Fetch user playlists
    playlists_r = requests.get('https://api.spotify.com/v1/me/playlists', headers=headers)
    playlists_json = playlists_r.json()
   
    playlists_html = '<h2>Your Playlists:</h2><ul>'
    for playlist in playlists_json.get('items', []):
        if(playlist.get("owner").get("id") == profile_json.get("id")): #get playlist created by the user 
            playlists_html += f'<li>{playlist.get("name")}</li>'
    playlists_html += '</ul>'
    result= f'''
    <!DOCTYPE html>
    <html lang="en" dir="ltr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0"> 
        <title>Spotify Profile</title>
        <link rel="stylesheet" type="text/css" href="{url_for('static', filename='styles.css')}">
    </head>
    <body>
        <div class="loader-container">
            <!-- Updated Loader -->
            <div class="loader">
                <div class="box box0">
                    <div></div>
                </div>
                <div class="box box1">
                    <div></div>
                </div>
                <div class="box box2">
                    <div></div>
                </div>
                <div class="box box3">
                    <div></div>
                </div>
                <div class="box box4">
                    <div></div>
                </div>
                <div class="box box5">
                    <div></div>
                </div>
                <div class="box box6">
                    <div></div>
                </div>
                <div class="box box7">
                    <div></div>
                </div>
                <div class="ground">
                        <div></div>
                </div>
            </div>
        </div>


        <div class="content" id="content">
            <h1>Hello, {profile_json.get("display_name")}!</h1>
            {playlists_html}
              <a href="/welcome">
            <button> <span>Back</span>
            </button> </a>
        </div>

        <script src="{url_for('static', filename='login.js')}"></script>
    </body>
    </html>
    '''

    return result


"Recently played song "
@app.route('/recently_played')
def recently_played():
    
    access_token = get_access_token()
    print(access_token)

    if not access_token:
        return redirect(url_for('login'))
    # Fetch user profile information
    headers = {'Authorization': f'Bearer {access_token}'}
    profile_r = requests.get('https://api.spotify.com/v1/me', headers=headers)
    profile_json = profile_r.json()
    # Fetch user playlists
    
    recently_played_tracks = []
    limit = 50
    total_items = 50
    offset = 0
    while len(recently_played_tracks) < total_items:
        response = requests.get(
            'https://api.spotify.com/v1/me/player/recently-played',
            headers=headers,
            params={'limit': limit, 'offset': offset}
        )
        if response.status_code != 200:
            return f"Failed to retrieve data: {response.status_code}, {response.text}"

        data = response.json()
        items = data.get('items', [])
        recently_played_tracks.extend(items)

        if len(items) < limit:
            # No more items available
            break

        offset += limit
 
    playlists_html = '<h2> Replay: The Last 50:</h2><ul>'
    for playlist in recently_played_tracks :
        song_name = playlist['track']['name']
        song_artist = playlist['track']['artists'][0]['name']
        play_time = playlist['played_at']
        # Convert play_time to a datetime object
        play_time_obj = datetime.fromisoformat(play_time[:-1])  

        # Convert to UTC
        play_time_utc = pytz.utc.localize(play_time_obj)
        # Convert UTC to Winnipeg time
        play_time_winnipeg = play_time_utc.astimezone(pytz.timezone('America/Winnipeg'))
        # Separate date and time
        formatted_date = play_time_winnipeg.date().strftime("%m/%d/%Y")
        formatted_time = play_time_winnipeg.time().strftime("%I:%M %p")
        
        song_result= f"Song Name: {song_name} by {song_artist} on {formatted_date} at {formatted_time}"

        playlists_html += f'<li>{song_result}</li>'
    playlists_html += '</ul>'
    result= f'''
    <!DOCTYPE html>
    <html lang="en" dir="ltr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0"> 
        <title>Spotify Profile</title>
        <link rel="stylesheet" type="text/css" href="{url_for('static', filename='styles.css')}">
    </head>
    <body>
        <div class="loader-container">
            <!-- Updated Loader -->
            <div class="loader">
                <div class="box box0">
                    <div></div>
                </div>
                <div class="box box1">
                    <div></div>
                </div>
                <div class="box box2">
                    <div></div>
                </div>
                <div class="box box3">
                    <div></div>
                </div>
                <div class="box box4">
                    <div></div>
                </div>
                <div class="box box5">
                    <div></div>
                </div>
                <div class="box box6">
                    <div></div>
                </div>
                <div class="box box7">
                    <div></div>
                </div>
                <div class="ground">
                        <div></div>
                </div>
            </div>
        </div>


        <div class="content" id="content">
            <h1>Hello, {profile_json.get("display_name")}!</h1>
            {playlists_html}
              <a href="/welcome">
            <button> <span>Back</span>
            </button> </a>
        </div>

        <script src="{url_for('static', filename='login.js')}"></script>
    </body>
    </html>
    '''

    return result

"Profile "
@app.route('/user_profile')
def user_profile():
    access_token = get_access_token()
    if not access_token:
        return None
    headers = {'Authorization': f'Bearer {access_token}'}
    profile_r = requests.get('https://api.spotify.com/v1/me', headers=headers)
    profile_json = profile_r.json()
    current_user_name= profile_json.get("display_name")
    current_user_email= profile_json.get("email")
    current_user_img= profile_json.get("images")
    if current_user_img:
        img_url = current_user_img[0].get("url")
    else:
        img_url = url_for('static', filename='user-solid.svg')
   
    
    result= f'''
    <!DOCTYPE html>
            <html lang="en" dir="ltr">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0"> 
                <title> profile page | Spotify activity   </title> 
                    <link rel="stylesheet" type="text/css" href="{url_for('static', filename='Profile.css')}">
            </head>
            <body>
                <div class="container">  
                <h1>Hello, {profile_json.get("display_name")}!</h1>
                <a href="/logout">
                <button> <span>Logout</span>
                </button> </a>
                <ul class="nav-links">
                    <li id="openModal" ><a href=#>Profile</a></li>
                    <li class="center"><a href="/profile">Playlists</a></li>
                    <li class="upward"><a href="/recently_played">Recently played</a></li>
                    <li class="forward"><a href="/store_play">Statistics</a></li>
                </ul>
                </div>
             <!-- Modal structure -->
            <div id="myModal" class="modal">
                <div class="modal-content">
                <span class="close">&times;</span>
                <h2>User Profile Information</h2>

                <!-- Profile Information -->
                <div class="profile-info">
                    
                    <div class="icon"> 
                    <img src="{img_url}" alt="Logo">
                    </div>
                    <div class="profile-text">
                    <p><strong>Name:</strong> {current_user_name}</p>
                    <p><strong>Email:</strong> {current_user_email}/p>
                   
                    </div>
                    
                </div>
                <!-- Permission Section -->
                <div class="permission-section">
                    <p>Do you grant permission?</p>
                    <div class="buttons">
                    <button class="yes-button">Yes</button>
                    <button class="no-button">No</button>
                    </div>
                </div>


                </div>
                </div>

            <script src="{{ url_for('static', filename='profile.js') }}"></script>
            </body>
            </html>
        '''


    return result



'''
---------------------------------------------------------------------------------------------------------------------------------------------------

playlists activity

---------------------------------------------------------------------------------------------------------------------------------------------------
'''
def create_playlist():
    access_token = get_access_token()
    print("create playlist token: ", access_token)
    if not access_token:
        return None
    headers = {'Authorization': f'Bearer {access_token}'}

   
    
    playlist_id = None
    playlist_name = "Morning playlist"
    playlist_exists = False
    # Spotify API paginates playlists, so we may need to retrieve them in multiple requests
    limit = 50  # Number of playlists to retrieve per request
    offset = 0  # Starting point for each request
    while not playlist_exists:
        playlists_response = requests.get('https://api.spotify.com/v1/me/playlists', headers=headers ,
                                params={'limit': limit, 'offset': offset} )
        if playlists_response.status_code != 200:
                print(f'failed to retrieve data: {playlists_response.status_code}, {playlists_response.text}')
                return
    
        playlists_data = playlists_response.json()
        playlists = playlists_data.get('items', [])
        # Check if a playlist with the same name already exists
        for playlist in playlists:
            user_playlistname = playlist['name']
            if str(user_playlistname).lower() == playlist_name.lower():
                playlist_exists = True
                playlist_id = playlist['id']
                print(f"A playlist with the name '{playlist_name}' already exists.")
                break
        
        # If there are no more playlists to fetch, break the loop
        if len(playlists) < limit:
            break
        
        # Increment the offset to get the next set of playlists
        offset += limit
    if not playlist_exists:
        playlist_description = "A playlist created using the Spotify API."

        create_playlist_data = {
            "name": playlist_name,
            "description": playlist_description,
            "public": False  # Set to True if you want the playlist to be public
        }

        create_playlist_response = requests.post(
        'https://api.spotify.com/v1/me/playlists',
            headers=headers,
            json=create_playlist_data
        )

        if create_playlist_response.status_code != 201:
            print(f"Failed to create playlist: {create_playlist_response.status_code}, {create_playlist_response.text}")
            return

        playlist_data = create_playlist_response.json()
        playlist_id = playlist_data['id']
        print(f"Playlist '{playlist_name}' created successfully with ID: {playlist_id}")
    return playlist_id



def Playlist_all_users_plays():
    '''
    Create a playlist for each user in the database.

    This function iterates over all users in the database, and for each user with the 'yes' permission,
    creates a playlist with the user's name and stores the playlist ID in the user's document.

    '''
    user_acess_token,user_refresh_token,token_expiry,user_permission=get_user_access_token(user_name)

    current_user_name= user_name
    user_permissions= user_permission
    if str(user_permissions).lower().strip() == 'yes':
        print('creating playlist for: ',current_user_name)
        playlist_id=create_playlist()
        if playlist_id is None:
            print("Error creating playlist for ",current_user_name)
            
        check_for_playlist(current_user_name,playlist_id)
        print("creating playlist  done for ",current_user_name)
    else:
        print("no permission to create playlist for: ",current_user_name)


def add_song_to_playlist():
    print("-------------------------------------------------------------------------------------------------------------------------------------------")
    Playlist_all_users_plays()
    access_token = get_access_token()
    print("add song to playlist token: ", access_token)
    if not access_token:
        return None
    headers = {'Authorization': f'Bearer {access_token}'}
    user_acess_token,user_refresh_token,token_expiry,user_permission=get_user_access_token(user_name)

    
    current_user_name= user_name
    user_permissions= user_permission
    
    try:  
        if  str(user_permissions).lower().strip() == 'yes':
            user_playlistid= get_user_playlistid(current_user_name)

                # Check if playlist_id exists and is valid
            if not user_playlistid:
                print(f"User {current_user_name} does not have a valid playlist ID.")
                
            print("user playlist id: ",user_playlistid)
            song_list=get_playlist_tracks(current_user_name,user_playlistid)
            for song in song_list:
                song_id=song['_id']['song_id']
                add_song_data = {
            "uris": [f"spotify:track:{song_id}"]
            }
                print("sending song to spotify")
                add_song_response = requests.post(
                    f'https://api.spotify.com/v1/playlists/{user_playlistid}/tracks',
                    headers=headers,
                    json=add_song_data
                ) 
                if add_song_response.status_code != 201:
                    print(f"Failed to add tracks to playlist: {add_song_response.status_code}, {add_song_response.text}")
                else:
                    print(f"Tracks added to playlist '{user_playlistid}' successfully.")

        else:
            print("no permission to add song to playlist for: ",current_user_name)
    except Exception as e:
        print("add song to playlist error:",e)

    print("-------------------------------------------------------------------------------------------------------------------------------------------")

def adding_song_to_all_users():
    

    
    

    global user_name
    User_data= get_all_users()
    print("-------------------------------------------------------------------------------------------------------------------")
    for user in User_data:
        user_name= user['user_id']
        print('Adding song for: ',user_name)
        add_song_to_playlist()
       
        print("stor_play_job done for ",user_name)
      
    print("-------------------------------------------------------------------------------------------------------------------")       


        
'''
---------------------------------------------------------------------------------------------------------------------------------------------------

statistics

---------------------------------------------------------------------------------------------------------------------------------------------------
'''

'storing  recent plays' 


def  store_play_job():
    access_token = get_access_token()
    print("store play job token: ", access_token)
    
    
    if not access_token:
        print("No valid token available.FOr store play job")
        return 
    headers = {'Authorization': f'Bearer {access_token}'}

    recently_played_tracks = []
    limit = 50
    total_items = 50
    offset = 0
    while len(recently_played_tracks) < total_items:
        response = requests.get(
            'https://api.spotify.com/v1/me/player/recently-played',
            headers=headers,
            params={'limit': limit, 'offset': offset}
        )
        if response.status_code != 200:
            return f"Failed to retrieve data: {response.status_code}, {response.text}"

        data = response.json()
        items = data.get('items', [])
        recently_played_tracks.extend(items)

        if len(items) < limit:
            # No more items available
            break

        offset += limit
    profile_r = requests.get('https://api.spotify.com/v1/me', headers=headers)
    profile_json = profile_r.json()
    user_name= profile_json.get('display_name')

    print(len(recently_played_tracks))
    count = 0
    # Store each play in MongoDB
    for item in recently_played_tracks:
        song_name = item['track']['name']
        song_id = item['track']['id']
        play_time = item['played_at']
        artists_name = item['track']['artists'][0]['name']
        store_recent_play(song_name, song_id, play_time,user_name,artists_name)
    now = datetime.now()

   # Convert to UTC
    play_time_utc = pytz.utc.localize(now)

    # Convert UTC to Winnipeg time
    current_time_winnipeg = play_time_utc.astimezone(pytz.timezone('America/Winnipeg'))

    # Format Winnipeg time as HH:MM:SS
    current_time_winnipeg_str = current_time_winnipeg.strftime("%H:%M:%S")
   
    print("Current Time =", current_time_winnipeg_str)
    print("Recent plays stored successfully.")



@app.route('/store_play')
def store_play():
    #store_play_job()
    

    
    
    result= f'''
    <!DOCTYPE html>
    <html lang="en" dir="ltr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0"> 
        <title>Welcome page</title>
        <link rel="stylesheet" type="text/css" href="{url_for('static', filename='stats.css')}">

    </head>
    <body>
    
      <div class="container">
            <div class="loader" id="loader"></div>
            <div class="content" id="content">
                <nav class="navbar">
                    <div class="logo">
                        <img src="{url_for('static', filename='logo.svg')}" alt="Logo">
                    </div>
                    <a href="/welcome">
                    <button> <span>Back</span>
                    </button> </a>
                    <ul class="nav-links">
                        <li><a href="/top_tracks">Top Tracks</a></li>
                        <li><a href="/top_artists">Top Artists</a></li>
                        <li><a href="/recent_plays">Listening activity</a></li>
                    </ul>
                </nav>
            </div>
        </div>
        <!-- Loader -->
    <script src="{url_for('static', filename='script.js')}"></script>
    
    </body>
    </html>
    '''
    return result


@app.route('/top_artists')
def top_artists():
    access_token = get_access_token()
    time_range = request.args.get('time_range', 'short_term')  # Default to 'medium_term' if not specified
    date='Last 4 Weeks'
    if time_range == 'short_term':
        date = 'Last 4 Weeks'
    elif time_range == 'medium_term':
        date = 'Last 6 Months'
    elif time_range == 'long_term':
        date = 'All Year'
    
    if not access_token:
        return redirect(url_for('login'))

    headers = {'Authorization': f'Bearer {access_token}'}
    top_tracks = [] #stored result  
    limit = 50
    total_items = 50
    offset = 0
    while len(top_tracks) < total_items:
        response = requests.get(
            'https://api.spotify.com/v1/me/top/artists',
            headers=headers,
           params={'limit': limit, 'offset': offset, 'time_range': time_range}
        )
        if response.status_code != 200:
            return f"Failed to retrieve data: {response.status_code}, {response.text}"

        data = response.json()
        items = data.get('items', [])
        top_tracks.extend(items)

        if len(items) < limit:
            # No more items available
            break

        offset += limit
    count = 0
   
   
    playlist_html= ''
      # Add rows with track details
    for i in range(0, len(top_tracks), 3):
        playlist_html += '<tr>'
        for j in range(3):
            if i + j < len(top_tracks):
                track = top_tracks[i + j]
                artist_name = track['name']
                Artist_image = track['images'][0]['url']
                Artist_url = track['external_urls']['spotify']
                count += 1
                playlist_html += f'''
                    <td>
                        <div class="track-item">
                            <a href="{Artist_url}" target="_blank">
                                <img src="{Artist_image}" alt="{artist_name}" class="track-img">
                                <div class="track-name">{count}. {artist_name}</div>
                            </a>
                        </div>
                    </td>
                '''
        playlist_html += '</tr>'

    result= f'''
        <!DOCTYPE html>
        <html lang="en" dir="ltr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0"> 
            <title>Welcome page</title>
            <link rel="stylesheet" type="text/css" href="{url_for('static', filename='toptrack.css')}">

        </head>
        <body>
        
        <div class="container">
                <div class="loader" id="loader"></div>
                <div class="content" id="content">
                    <div class="page">
                        <nav class="navbar">
                            <div class="logo">
                                <img src="{url_for('static', filename='logo.svg')}" alt="Logo">
                            </div>
                            <a href="/welcome">
                            <button class ="return-button"> <span>Back</span>
                            </button> </a>
                            <ul class="nav-links">
                                <li><a href="/top_tracks">Top Tracks</a></li>
                                <li><a href="/top_artists">Top Artists</a></li>
                                <li><a href="/recent_plays">Listening activity</a></li>
                            </ul>
                        </nav>
                    </div>
                    <h2>Top Tracks ({date}) </h2>
                                    
                         <!-- Button elements -->
                    
                        <a href="/top_artists?time_range=short_term"> <button class="fourweeks-btn"> <span>Last 4 weeks</span></button> </a>
                       <a href="/top_artists?time_range=medium_term"><button class="sixmonths-btn"> <span>Last 6 months</span></button> </a>
                        <a href="/top_artists?time_range=long_term"><button class="twelvemonths-btn"> <span>Last 12 months</span></button></a>

                    <div class="tracks">
                           <table class="track-table">
                            {playlist_html}    
                            </table>
                    </div>
                   
                
                    
            </div>
        </div>
            <!-- Loader -->
        <script src="{url_for('static', filename='script.js')}"></script>
        
        </body>
        </html>
        '''
    return result


@app.route('/top_tracks')
def top_tracks():
    access_token = get_access_token()
    time_range = request.args.get('time_range', 'short_term')  # Default to 'medium_term' if not specified
    date='Last 4 Weeks'
    if time_range == 'short_term':
        date = 'Last 4 Weeks'
    elif time_range == 'medium_term':
        date = 'Last 6 Months'
    elif time_range == 'long_term':
        date = 'All Year'
    
    if not access_token:
        return redirect(url_for('login'))

    headers = {'Authorization': f'Bearer {access_token}'}
    top_tracks = [] #stored result  
    limit = 50
    total_items = 50
    offset = 0
    while len(top_tracks) < total_items:
        response = requests.get(
            'https://api.spotify.com/v1/me/top/tracks',
            headers=headers,
           params={'limit': limit, 'offset': offset, 'time_range': time_range}
        )
        if response.status_code != 200:
            return f"Failed to retrieve data: {response.status_code}, {response.text}"

        data = response.json()
        items = data.get('items', [])
        top_tracks.extend(items)

        if len(items) < limit:
            # No more items available
            break

        offset += limit
    count = 0
   
   
    playlist_html= ''
      # Add rows with track details
    for i in range(0, len(top_tracks), 3):
        playlist_html += '<tr>'
        for j in range(3):
            if i + j < len(top_tracks):
                track = top_tracks[i + j]
                track_name = track['name']
                artist_name = track['artists'][0]['name']
                album_image = track['album']['images'][0]['url']
                track_url = track['external_urls']['spotify']
                count += 1
                playlist_html += f'''
                    <td>
                        <div class="track-item">
                            <a href="{track_url}" target="_blank">
                                <img src="{album_image}" alt="{track_name}" class="track-img">
                                <div class="track-name">{count}. {track_name} by {artist_name}</div>
                            </a>
                        </div>
                    </td>
                '''
        playlist_html += '</tr>'

    result= f'''
        <!DOCTYPE html>
        <html lang="en" dir="ltr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0"> 
            <title>Welcome page</title>
            <link rel="stylesheet" type="text/css" href="{url_for('static', filename='toptrack.css')}">

        </head>
        <body>
        
        <div class="container">
                <div class="loader" id="loader"></div>
                <div class="content" id="content">
                    <div class="page">
                        <nav class="navbar">
                            <div class="logo">
                                <img src="{url_for('static', filename='logo.svg')}" alt="Logo">
                            </div>
                            <a href="/welcome">
                            <button class ="return-button"> <span>Back</span>
                            </button> </a>
                            <ul class="nav-links">
                                <li><a href="/top_tracks">Top Tracks</a></li>
                                <li><a href="/top_artists">Top Artists</a></li>
                                <li><a href="/recent_plays">Listening activity</a></li>
                            </ul>
                        </nav>
                    </div>
                    <h2>Top Tracks ({date}) </h2>
                                    
                         <!-- Button elements -->
                    
                        <a href="/top_tracks?time_range=short_term"> <button class="fourweeks-btn"> <span>Last 4 weeks</span></button> </a>
                       <a href="/top_tracks?time_range=medium_term"><button class="sixmonths-btn"> <span>Last 6 months</span></button> </a>
                        <a href="/top_tracks?time_range=long_term"><button class="twelvemonths-btn"> <span>Last 12 months</span></button></a>

                    <div class="tracks">
                           <table class="track-table">
                            {playlist_html}    
                            </table>
                    </div>
                   
                
                    
            </div>
        </div>
            <!-- Loader -->
        <script src="{url_for('static', filename='script.js')}"></script>
        
        </body>
        </html>
        '''
    return result





@app.route('/recent_plays')
def recent_plays():
    #store_play_job()
    access_token = get_access_token()
    #print("The access_token is",access_token);
    # print(session)
    if not access_token:
        return redirect(url_for('login'))
    # Fetch user profile information
    headers = {'Authorization': f'Bearer {access_token}'}
    profile_r = requests.get('https://api.spotify.com/v1/me', headers=headers)
    profile_json = profile_r.json()
    user_name= profile_json.get('display_name')

    recent_plays,recent_json=get_all_recent_plays(user_name)
    playlists_html = '<h2>Your Song History:</h2><ul>'
    for playlist in recent_plays:
        playlists_html += f'<li>{playlist}</li>'
    playlists_html += '</ul>'
    result= f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Spotify Profile</title>
        <link rel="stylesheet" type="text/css" href="{url_for('static', filename='styles.css')}">
    </head>
    <body>
        <div class="loader-container">
            <!-- Updated Loader -->
            <div class="loader">
                <div class="box box0">
                    <div></div>
                </div>
                <div class="box box1">
                    <div></div>
                </div>
                <div class="box box2">
                    <div></div>
                </div>
                <div class="box box3">
                    <div></div>
                </div>
                <div class="box box4">
                    <div></div>
                </div>
                <div class="box box5">
                    <div></div>
                </div>
                <div class="box box6">
                    <div></div>
                </div>
                <div class="box box7">
                    <div></div>
                </div>
                <div class="ground">
                        <div></div>
                </div>
            </div>
        </div>

        
        <div class="content" id="content">
            <h1>Hello, {profile_json.get("display_name")}!</h1>
            {playlists_html}
            <a href="/store_play">
            <button> <span>Back</span>
            </button> </a>
        </div>

        <script src="{url_for('static', filename='login.js')}"></script>
    </body>
    </html>
    '''

    return result





def store_all_users_plays():
    

    
    

    global user_name
    User_data= get_all_users()
    print("-------------------------------------------------------------------------------------------------------------------")
    for user in User_data:
        user_name= user['user_id']
        print('storing plays for: ',user_name)
        store_play_job()
       # check_for_playlist(user_name)
        print("stor_play_job done for ",user_name)
    print("-------------------------------------------------------------------------------------------------------------------")


def get_data(song_id):
    access_token = get_access_token()
    if not access_token:
        print("No valid token available.FOr change_data")
        return None

    headers = {'Authorization': f'Bearer {access_token}'}
    profile_r = requests.get(f'https://api.spotify.com/v1/tracks/{song_id}', headers=headers)
    song_json = profile_r.json()
    artist_name=song_json['artists'][0]['name']
    return artist_name


'''
---------------------------------------------------------------------------------------------------------------------------------------------------

ADmin Login

---------------------------------------------------------------------------------------------------------------------------------------------------

# Admin Authentication
def hash_password(password):
    """Generates a hash for the given password."""
    return generate_password_hash(password)

def verify_password(stored_password, provided_password):
    """Verifies the provided password against the stored hash."""
    return check_password_hash(stored_password, provided_password)

def register_admin(username, password):
    """Register a new admin with hashed password in the database."""
    hashed_password = hash_password(password)
    admin_data = {
        'username': username,
        'password': hashed_password
    }
    store_admin_user(admin_data)

def authenticate_admin(username, password):
    """Authenticate admin by checking username and password."""
    admin_user = get_admin_user(username)
    if admin_user and verify_password(admin_user['password'], password):
        return True
    return False
# Admin login route
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if authenticate_admin(username, password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return redirect(url_for('admin_dashboard'))
        else:
            print('Invalid credentials. Please try again.', 'danger')
    
    

    print("Welcome page")
    
'''


















# Ensure the scheduler is shut down when the app exits
atexit.register(lambda: scheduler.shutdown())

# Add job to scheduler to run every 25 minutes
scheduler.add_job(func=store_all_users_plays, trigger="interval", minutes=25)
winnipeg_tz = timezone('America/Winnipeg')

scheduler.add_job(func=adding_song_to_all_users, trigger='cron', day_of_week='fri', hour=0, minute=1, timezone=winnipeg_tz)

# Start the scheduler
start_scheduler()






if __name__ == '__main__':
    app.run(debug=True)
    
