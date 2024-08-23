from dotenv import load_dotenv
from flask import Flask, flash, redirect, request, session, url_for
import requests
import os
from datetime import datetime,timedelta
from .db_operations import store_recent_play, get_all_recent_plays
from apscheduler.schedulers.background import BackgroundScheduler
import pytz


# Load environment variables fclearom .env file
load_dotenv()
app = Flask(__name__)
app.secret_key = os.urandom(24)


# Replace these with your own Spotify credentials
SPOTIPY_CLIENT_ID = os.getenv('API_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('API_KEY')
SPOTIPY_REDIRECT_URI = 'https://testspotify-af120bb16cf3.herokuapp.com/callback'

# Spotify authorization URL
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'


# scheduler
scheduler = BackgroundScheduler()

# Global variable to store access token
global_access_token = None
# Global variables to store token data
global_access_token = None
global_refresh_token = None
token_expiry = None

def save_tokens(access_token, refresh_token, expires_in):
    global global_access_token, global_refresh_token, token_expiry
    global_access_token = access_token
    global_refresh_token = refresh_token
    token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)

def refresh_access_token():
    global global_refresh_token, global_access_token, token_expiry
    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': global_refresh_token,
        'client_id': SPOTIPY_CLIENT_ID,
        'client_secret': SPOTIPY_CLIENT_SECRET
    }
    response = requests.post(TOKEN_URL, data=payload)
    refreshed_tokens = response.json()
    access_token = refreshed_tokens.get('access_token')
    expires_in = refreshed_tokens.get('expires_in')
    new_refresh_token = refreshed_tokens.get('refresh_token', global_refresh_token)

    save_tokens(access_token, new_refresh_token, expires_in)
    return access_token

def get_access_token():
    if token_expiry is None:
        print("no token")
    else:
        if datetime.utcnow() >= token_expiry:
            return refresh_access_token()
    return global_access_token


@app.route('/')
def index():
    result= f'''
    <!DOCTYPE html>
    <html>
    <head>s
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
        'scope': 'user-library-read playlist-read-private playlist-read-collaborative user-read-recently-played'
    }
    auth_url = requests.Request('GET', AUTH_URL, params=auth_query).prepare().url
    return redirect(auth_url)

@app.route('/logout')
def logout():
    # Clear the session
    session.clear()

    # Optionally, add a logout message
    print('You have been logged out.', 'info')

    # Redirect to the login page or home page
    return redirect(url_for('index'))

@app.route('/callback')
def callback():
    global global_access_token

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


    save_tokens(access_token, refresh_token, expires_in)
    # Store access token in session
    session['access_token'] = access_token

    # Store access token in a global variable
    global_access_token = access_token

    # Start the scheduler after obtaining the access token
    scheduler.start()
    scheduler.add_job(store_play_job, 'interval', minutes=25)
    
    return redirect(url_for('welcome'))

"Welcome Page"
@app.route('/welcome')
def welcome():
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
    print(access_token)

    access_token = get_access_token()
 
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
              <a href="/welcome">
            <button> <span>Back</span>
            </button> </a>
        </div>

        <script src="{url_for('static', filename='login.js')}"></script>
    </body>
    </html>
    '''

    return result


'storing  recent plays' 


def  store_play_job():
    access_token = get_access_token()
    print(access_token)
    
    if not access_token:
        return redirect(url_for('login'))

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


    print(len(recently_played_tracks))
    count = 0
    # Store each play in MongoDB
    for item in recently_played_tracks:
        song_name = item['track']['name']
        song_id = item['track']['id']
        play_time = item['played_at']
        store_recent_play(song_name, song_id, play_time,count)
    now = datetime.now()

    current_time = now.strftime("%H:%M:%S")
    print("Current Time =", current_time)
    print("Recent plays stored successfully.")

@app.route('/store_play')
def store_play():

    store_play_job()
    result= f'''
    <!DOCTYPE html>
    <html>
    <head>
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
                        <li><a href="/recent_plays">Recently Played</a></li>
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

@app.route('/recent_plays')
def recent_plays():
    print(access_token)

    access_token = get_access_token()
    #print("The access_token is",access_token);
    # print(session)
    if not access_token:
        return redirect(url_for('login'))
    # Fetch user profile information
    headers = {'Authorization': f'Bearer {access_token}'}
    profile_r = requests.get('https://api.spotify.com/v1/me', headers=headers)
    profile_json = profile_r.json()
    recent_plays=get_all_recent_plays()
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
