from dotenv import load_dotenv
from flask import Flask, flash, redirect, request, session, url_for
import requests
import os
from datetime import datetime,timedelta
from .db_operations import store_recent_play, get_all_recent_plays,save_users_to_db,get_user_access_token,add_artist_name
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
import atexit



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
    user_acess_token,user_refresh_token,user_token_expiry=get_user_access_token(user_id)
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
    user_acess_token,user_refresh_token,token_expiry=get_user_access_token(user_name)

  
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
        'scope': 'user-library-read playlist-read-private playlist-read-collaborative user-read-recently-played user-top-read user-read-private user-read-email'
    }
    auth_url = requests.Request('GET', AUTH_URL, params=auth_query).prepare().url
    return redirect(auth_url)

@app.route('/logout')
def logout():
    # Clear the session
    session.clear()

    # Optionally, add a logout message
    print('You have been logged out.', 'info')
    user_name='fumnanya_obi' # Replace with the name of the user you want to log out
    # Redirect to the login page or home page
    return redirect(url_for('index'))
#removing the methode now the databased  has updated
''' 
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
@app.route('/callback')
def callback():
    global global_access_token, user_name,global_permissions,user_email

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

    # Extract user information
    if(profile_data.get('id') is not profile_data.get('display_name')):
        user_id=profile_data.get('display_name')
    else:
        user_id=profile_data.get('id') # Spotify user ID
    #user_id = profile_data.get('id')  
    email = profile_data.get('email')  # User email
    #print(profile_data)
    permission="yes"
    
    save_users_to_db(user_id, access_token, refresh_token, expires_in,email,permission)
   
    print("User information retrieved successfully. callback method")
    # Store access token in a global variable
    global_access_token = access_token
    user_name=user_id
    user_email=email
    global_permissions=permission

   


    return redirect(url_for('welcome'))

"Welcome Page"
@app.route('/welcome')
def welcome():
    print("Welcome page")
    access_token = get_access_token()
    print(access_token)
    if not access_token:
        return redirect(url_for('login'))
    headers = {'Authorization': f'Bearer {access_token}'}
    profile_r = requests.get('https://api.spotify.com/v1/me', headers=headers)
    profile_json = profile_r.json()
    result= f'''
        <!DOCTYPE html>
        <html lang="en" dir="ltr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0"> 
            <title> Welcome page | Spotify activity   </title> 
                <link rel="stylesheet" type="text/css" href="{url_for('static', filename='frontpage.css')}">
        </head>
        <body>
            <div class="container">  
            <h1>Hello, {profile_json.get("display_name")}!</h1>
            <a href="/logout">
            <button> <span>Logout</span>
            </button> </a>
            <ul class="nav-links">
                <li><a href="#">Profile</a></li>
                <li class="center"><a href="/profile">Playlists</a></li>
                <li class="upward"><a href="/recently_played">Recently played</a></li>
                <li class="forward"><a href="/store_play">Statistics</a></li>
            </ul>
            </div>


       
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

# Ensure the scheduler is shut down when the app exits
atexit.register(lambda: scheduler.shutdown())

# Add job to scheduler to run every 25 minutes
scheduler.add_job(func=store_play_job, trigger="interval", minutes=15)

# Start the scheduler
start_scheduler()

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


if __name__ == '__main__':
    app.run(debug=True)
