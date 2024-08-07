from dotenv import load_dotenv
from flask import Flask, redirect, request, session, url_for
import requests
import os
# Load environment variables fclearom .env file
load_dotenv()
app = Flask(__name__)
app.secret_key = os.urandom(24)


# Replace these with your own Spotify credentials
SPOTIPY_CLIENT_ID = os.getenv('API_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('API_KEY')
SPOTIPY_REDIRECT_URI = 'http://localhost:5000/callback'

# Spotify authorization URL
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'

@app.route('/')
def index():
    result= f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Welcome page</title>
        <link rel="stylesheet" type="text/css" href="{url_for('static', filename='welcome.css')}">

    </head>
    <body>
    
     <div class="container">
            <div class="loader" id="loader"></div>
            <div class="content" id="content">
                <h1>Welcome to the Spotify OAuth app!</h1>
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
        'scope': 'user-library-read playlist-read-private playlist-read-collaborative'
    }
    auth_url = requests.Request('GET', AUTH_URL, params=auth_query).prepare().url
    return redirect(auth_url)

@app.route('/callback')
def callback():
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
    token_r = requests.post(TOKEN_URL, data=token_data)
    token_json = token_r.json()
    print(token_json)
    access_token = token_json.get('access_token')

    if not access_token:
        return 'Failed to retrieve access token.'

    # Store access token in session
    session['access_token'] = access_token
    return redirect(url_for('profile'))

@app.route('/profile')
def profile():
    access_token = session.get('access_token')
    #print("The access_token is",access_token);
    # print(session)
    if not access_token:
        return redirect(url_for('login'))
    # Fetch user profile information
    headers = {'Authorization': f'Bearer {access_token}'}
    profile_r = requests.get('https://api.spotify.com/v1/me', headers=headers)
    profile_json = profile_r.json()
   # print(profile_json)
    # Fetch user playlists
    playlists_r = requests.get('https://api.spotify.com/v1/me/playlists', headers=headers)
    playlists_json = playlists_r.json()
    # test= playlists_json.get('items', [])
    # for testlist in test:
    #     ownerlist= testlist.get("owner")
    #     print(ownerlist)
    # Generate HTML content for playlists
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
        </div>

        <script src="{url_for('static', filename='login.js')}"></script>
    </body>
    </html>
    '''

    return result

if __name__ == '__main__':
    app.run(debug=True)
