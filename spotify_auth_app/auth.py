from dotenv import load_dotenv
from flask import Flask, flash, jsonify, redirect, request, session, url_for,render_template
import requests
import os
from datetime import datetime,timedelta
from .db_operations import store_recent_play,get_all_recent_plays,save_users_to_db,get_user_access_token,get_all_users,check_for_playlist,get_playlist_tracks,update_user_permissions,get_user_playlistid,delete_old_songs, check_song_from_playlist, get_admin_user,store_admin_user, store_log_details,get_log_details,store_new_user
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
SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI')



# Spotify authorization URL
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'


# variable to store user data





# Function to start the scheduler if it's not already running
def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        print("Scheduler started.")


def refresh_access_token( user_id):
    user_acess_token,user_refresh_token,token_expiry,user_permission,user_email=get_user_access_token(user_id)
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
        save_users_to_db(user_id, access_token, new_refresh_token, expires_in,user_email,user_permission)
        print("refresh_access_token method")
        print(f"Access token refreshed: {access_token}")
        print(f"Refresh token refreshed: {new_refresh_token}")
        return access_token, new_refresh_token
    else:
        print(f"Failed to refresh access token: {response.status_code}, {response.text}")
        return None
def get_access_token(user_name):
    print("get_access_token method: ", user_name)
    user_acess_token,user_refresh_token,token_expiry,user_permission,user_email=get_user_access_token(user_name)

  
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
   
    return redirect(url_for('front_page'))

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
    store_log_details(user_name,'User logged out')

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
        store_log_details(user_name,'Failed to retrieve access token.')
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
   
    
    # Redirect to the welcome page
    session['user'] = user_name
    store_log_details(user_name,'User logged in')


    return redirect(url_for('welcome'))
@app.route('/front_page')
def front_page():
  
    
    result= f'''
    <!DOCTYPE html>
    <html lang="en" dir="ltr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0"> 
        <title>Statistics</title>
        <link rel="stylesheet" type="text/css" href="{url_for('static', filename='front.css')}">

    </head>
    <body>
    
      <div class="container">
            <div class="loader" id="loader"></div>
            <div class="content" id="content">
                <nav class="navbar">
                    <div class="logo">
                        <img src="{url_for('static', filename='logo.svg')}" alt="Logo">
                    </div>
                    <a href="/login">
                    <button> <span>Login</span>
                    </button> </a>
                    <ul class="nav-links">
                        <li><a href="#">Users Top Tracks</a></li>
                        <li><a href="#">Users Top Artists</a></li>
                        <li><a href="#">Users Top Genres</a></li>
                        <li><a href="#">Users Playlists</a></li>
                        <li><a href="/new_users">New Users</a></li>
                       
                    </ul>
                </nav>
                 
            </div>
            <div class="overlay" id="overlay" >
            <h1>Welcome to Your Spotify Stats</h1>
            <p>Log in with Spotify to view your personalized music insights.</p>
            </div>
        </div>
        <!-- Loader -->
    <script src="{url_for('static', filename='front.js')}"></script>
    
    </body>
    </html>
    '''
    return result
@app.route("/submit_spotify_ID", methods=["POST"])
def submit():
    data = request.get_json()

    # Extract Spotify ID and email
    spotify_id = data.get("spotifyId")
    email = data.get("email")

    # Validation
    if not spotify_id or not email:
        return jsonify({"message": "Spotify ID and email are required!"}), 400

    # Insert into MongoDB
    submission = {"spotifyId": spotify_id, "email": email}
    store_new_user(submission)
    

    return jsonify({"message": "Submission successful!","redirect_url": url_for("success")}), 200
@app.route("/success")
def success():
    return redirect(url_for('front_page'))


@app.route('/new_users')
def new_users():
    result= f'''
    <!DOCTYPE html>
    <html lang="en" dir="ltr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0"> 
        <title>Statistics</title>
        <link rel="stylesheet" type="text/css" href="{url_for('static', filename='newusers.css')}">

    </head>
    <body>
    
      <div class="container">
            <div class="loader" id="loader"></div>
            <div class="content" id="content">
                <nav class="navbar">
                    <div class="logo">
                        <img src="{url_for('static', filename='logo.svg')}" alt="Logo">
                    </div>
                    <a href="/login">
                    <button class="logout-button" > <span>Login</span>
                    </button> </a>
                    <ul class="nav-links">
                       
                       
                    </ul>
                </nav>
                 
            </div>
             <div class="Report" id="Report">
            
                    <form class="form" id="spotifyForm">
                    <p class="form-title">Submit Spotify ID</p>
                        <div class="input-container">
                         <input id="spotifyId" name="spotifyId" placeholder="Spotify ID" type="text" required>
                        
                    </div>
                    <div class="input-container">
                        <input id="email" name="email" placeholder="Email" type="email" required>


                        </div>
                        <button class="submit" type="submit">
                        Submit
                    </button>

                    <p class="signup-link">
                       Need help?
                        <a href="https://community.spotify.com/t5/FAQs/Finding-login-details/ta-p/5182392#:~:text=Find%20your%20profile%20via%20search,si%3D%22%20is%20your%20ID.">Spotify FAQ</a>
                    </p>
                </form>

             
             </div>
       
        </div>
        <!-- Loader -->
    <script src="{url_for('static', filename='newusers.js')}"></script>
    
    </body>
    </html>
    '''
    return result
@app.route('/submit_permission', methods=['POST'])
def submit_permission():
    try:
        user_name = session.get('user')
        if session.get('admin_logged_in'):
            data = request.json
            user_name = data['user_name']
            print(user_name)
            response = 'Yes' if data['response'] else 'no'  # Convert boolean to string

            # Update user permissions
            update_user_permissions(user_name, response)

            # Log the detail
            detail = f"Permission updated: {response}"
            store_log_details(user_name, detail)
        else:
            data = request.json
            update_user_permissions(user_name,data['response'])
            detail="Permission updated: "+data['response']
            store_log_details(user_name,detail)
        return jsonify({'status': response})  
    except Exception as e:
        print(e)
        return jsonify({'status': str(e)}), 500
"Welcome Page"
@app.route('/welcome')
def welcome():
    print("Welcome page")
    current_user=session.get('user')
    user_acess_token,user_refresh_token,token_expiry,user_permission,user_email=get_user_access_token(current_user)
    response=user_permission
    access_token = get_access_token(current_user)
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
            <button class="logout-button"> <span>Logout</span>
            </button> </a>
            <a href="/front_page">
            <button class="back-button" ><span>Back</span>
            </button> </a>
            <div class="Admin">
            <a href="{url_for('admin_login')}">
            <p> Admin</p>
            </a>
            </div>
            <ul class="nav-links">
                 <li id="openModal" ><a href=#>Profile</a></li>
                <li class="center"><a href="/playlist">Playlists</a></li>
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



@app.route('/playlist')
def profile():
    print("Profile page")
    current_user=session.get('user')
    access_token = get_access_token(current_user)
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
        playlist_url=playlist.get("external_urls").get("spotify")
        if(playlist.get("owner").get("id") == profile_json.get("id")): #get playlist created by the user 
            playlists_html += f'<li><a href="{playlist_url}">{playlist.get("name")}</a></li>'
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
    
    current_user=session.get('user')
    access_token = get_access_token(current_user)
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
    
    current_user=session.get('user')
    access_token = get_access_token(current_user)
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
                    <li class="center"><a href="/playlist">Playlists</a></li>
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
def create_playlist(current_user):
    access_token = get_access_token(current_user)
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
                store_log_details(current_user, f"failed to retrieve data, {playlists_response.status_code}, {playlists_response.text}")
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
        store_log_details(current_user,f"Playlist '{playlist_name}' created successfully with ID: {playlist_id}")
    return playlist_id



def Playlist_all_users_plays(current_user):
    '''
    Create a playlist for each user in the database.

    This function iterates over all users in the database, and for each user with the 'yes' permission,
    creates a playlist with the user's name and stores the playlist ID in the user's document.

    '''
    user_acess_token,user_refresh_token,token_expiry,user_permission,user_email=get_user_access_token(current_user)


    current_user_name= current_user
    user_permissions= user_permission
    if str(user_permissions).lower().strip() == 'yes':
        print('creating playlist for: ',current_user_name)
        playlist_id=create_playlist(current_user)
        if playlist_id is None:
            print("Error creating playlist for ",current_user_name)
            store_log_details(current_user,f"Error creating playlist for {current_user_name}")
        else:   
            check_for_playlist(current_user_name,playlist_id)
            print("creating playlist  done for ",current_user_name)
            #store_log_details(current_user,f"creating playlist  done for {current_user_name}")
    else:
        print("no permission to create playlist for: ",current_user_name)


def add_song_to_playlist(current_user):
    print("-------------------------------------------------------------------------------------------------------------------------------------------")
    Playlist_all_users_plays(current_user)
    access_token = get_access_token(current_user)
    print("add song to playlist token: ", access_token)
    if not access_token:
        return None
    headers = {'Authorization': f'Bearer {access_token}'}
    user_acess_token,user_refresh_token,token_expiry,user_permission,user_email=get_user_access_token(current_user)


    
    current_user_name= current_user
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
                song_name = song['_id']['song_name'] 
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
                    store_log_details(current_user_name,f"Failed to add tracks to playlist: {add_song_response.status_code}, {add_song_response.text}")
                else:
                    print(f"Tracks added to playlist '{user_playlistid}' successfully.")
                    store_log_details(current_user_name,f"Track '{song_name}' Added to playlist '{user_playlistid}' successfully." )


        else:
            print("no permission to add song to playlist for: ",current_user_name)
    except Exception as e:
        print("add song to playlist error:",e)

    print("-------------------------------------------------------------------------------------------------------------------------------------------")















def adding_song_to_all_users():
    User_data= get_all_users()
    print("-------------------------------------------------------------------------------------------------------------------")
    for user in User_data:
        user_name= user['user_id']
        print('Deleting song for: ',user_name)
        print('DELETING song for: ',user_name)
        delete_song_from_playlist(user_name)
        print('Adding song for: ',user_name)
        add_song_to_playlist(user_name)
       
        print("Adding song job done for ",user_name)
      
    print("-------------------------------------------------------------------------------------------------------------------")       

def delete_song_from_playlist(current_user):
    print("-------------------------------------------------------------------------------------------------------------------------------------------")
    access_token = get_access_token(current_user)
    print("delete song from playlist token: ", access_token)
    
    if not access_token:
        return None
    
    headers = {'Authorization': f'Bearer {access_token}'}
    user_acess_token, user_refresh_token, token_expiry, user_permission, user_email = get_user_access_token(current_user)
    
    current_user_name = current_user
    user_permissions = user_permission
    
    try:  
        if str(user_permissions).lower().strip() == 'yes':
            user_playlistid = get_user_playlistid(current_user_name)

            # Check if playlist_id exists and is valid
            if not user_playlistid:
                print(f"User {current_user_name} does not have a valid playlist ID.")
                return None
                
            print("user playlist id: ", user_playlistid)
            
            song_list = delete_old_songs(current_user_name)
             # Break early if song_list is None or empty
            if not song_list:
                print(f"No songs found for deletion in playlist '{user_playlistid}'.")
                return None
            for song in song_list:
                song_id = song['_id']['song_id']
                song_name = song['_id']['song_name'] 
                
                delete_song_data = {
                    "tracks": [{"uri": f"spotify:track:{song_id}"}]
                }

                print("sending request to delete song from spotify")
                delete_song_response = requests.delete(
                    f'https://api.spotify.com/v1/playlists/{user_playlistid}/tracks',
                    headers=headers,
                    json=delete_song_data
                )

                if delete_song_response.status_code != 200:
                    print(f"Failed to delete track from playlist: {delete_song_response.status_code}, {delete_song_response.text}")
                else:
                    print(f"Track '{song_id}' removed from playlist '{user_playlistid}' successfully.")
                    store_log_details(current_user_name,f"Track '{song_name}' removed from playlist '{user_playlistid}' successfully." )
        
        else:
            print(f"No permission to delete songs from playlist for: {current_user_name}")

    except Exception as e:
        print(f"delete song from playlist error: {e}")
    
    print("-------------------------------------------------------------------------------------------------------------------------------------------")


'''
---------------------------------------------------------------------------------------------------------------------------------------------------

statistics

---------------------------------------------------------------------------------------------------------------------------------------------------
'''

'storing  recent plays' 


def  store_play_job(current_user):

    access_token = get_access_token(current_user)
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
  
    
    result= f'''
    <!DOCTYPE html>
    <html lang="en" dir="ltr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0"> 
        <title>Statistics</title>
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
    current_user=session.get('user')
    access_token = get_access_token(current_user)
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
    current_user=session.get('user')
    print(current_user)
    access_token = get_access_token(current_user)
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
   
    current_user=session.get('user')
    access_token = get_access_token(current_user)
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

    User_data= get_all_users()
    print("-------------------------------------------------------------------------------------------------------------------")
    for user in User_data:
        user_name= user['user_id']
        print('storing plays for: ',user_name)
        store_play_job(user_name)
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


    
'''

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
    store_admin_user(admin_data)  # This should store the admin details in the database
    print('Admin registered successfully!')
   

def authenticate_admin(username, password):
    """Authenticate admin by checking username and password."""
    admin_user = get_admin_user(username)  # Retrieve admin user data from the database
   
    if admin_user and verify_password(admin_user['password'], password):
        print('Admin authenticated successfully!')
        return True
    else:
        print('Admin authentication failed!')
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
            store_log_details(session['admin_username'], "Login")
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('admin_login.html')

# Admin dashboard route
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html')

# Admin logout route
@app.route('/admin/logout')
def admin_logout():
    flash('You have been logged out.', 'info')
    store_log_details(session['admin_username'], "Logout")
    session.clear()

    return redirect(url_for('admin_login'))

# Admin report route
@app.route('/admin/report')
def admin_report():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
   

   
    report_list= get_log_details()
    report_html=''
    index=0
    for i in report_list:
        report_html+=f"<tr><td>{index+1}</td><td>{i['User_name']}</td><td>{i['Details']}</td><td>{i['Date']} {i['Time']}</td></tr>"
        index+=1
    return render_template('admin_report.html',report_list=report_html)
@app.route('/get_permission_status/<user_name>', methods=['GET'])
def get_permission_status(user_name):
    try:
        # Fetch the last permission status for the user
        user_acess_token, user_refresh_token, token_expiry, user_permission, user_email = get_user_access_token(user_name)
        switchid = request.args.get('switchid')  # Get switchid from query params

        return jsonify({'user_name': user_name, 'user_permission': user_permission ,'switchid':switchid }), 200
    except Exception as e:
        print(f'Error fetching permission: {e}')
        return jsonify({'status': 'error', 'error': str(e)}), 500

# Admin registration route (optional, you can disable this in production)
@app.route('/admin/Access')
def admin_access():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    User_data= get_all_users()
    
    playlist_html=''
    count=1
    for user in User_data:
        user_name= user['user_id']
        switch_id = f'switch{count}'
        get_permission_status(user_name)
        playlist_html+=f'''<tr>
                    <td>
                        <p>
                        {user_name}
                        
                        </p>
                    </td>
                    <td>
                        <label class="switch-button" for="{switch_id }">
                            <div class="switch-outer">
                              <input id="switch{count}" type="checkbox" 
                                onchange="updatePermission('{user_name}', this.checked)">
                              <div class="button">
                                <span class="button-toggle"></span>
                                <span class="button-indicator"></span>
                              </div>
                            </div>
                          </label>
                    </td>
                    
                </tr>
                '''
        print(f"<u{user_name}: switch{count}>)")
        count+=1

    return render_template('admin_access.html',playlist_html=playlist_html)





@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
     # Ensure the user is logged in and an admin
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        register_admin(username, password)
        flash('Admin registered successfully!', 'success')
        store_log_details(username, "Registered successfully as an admin")
        return redirect(url_for('admin_login'))

    return render_template('admin_register.html')



@app.route('/admin/functions', methods=['GET', 'POST'])
def admin_functions():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    adding_song_to_all_users()
    return redirect(url_for('admin_dashboard'))











# Ensure the scheduler is shut down when the app exits
atexit.register(lambda: scheduler.shutdown())

# Add job to scheduler to run every 25 minutes
scheduler.add_job(func=store_all_users_plays, trigger="interval", minutes=25)
winnipeg_tz = timezone('America/Winnipeg')

scheduler.add_job(func=adding_song_to_all_users, trigger='cron', day_of_week='fri', hour=0, minute=5, timezone=winnipeg_tz)

# Start the scheduler
start_scheduler()




if __name__ == '__main__':
    app.run(debug=True)
    
