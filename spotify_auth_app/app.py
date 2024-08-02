# app.py
from flask_session import Session
from flask import Flask, redirect, request, session, url_for
from requests_oauthlib import OAuth2Session
import os
import requests
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()


# Configuration
CLIENT_ID = os.getenv('API_ID')
CLIENT_SECRET = os.getenv('API_KEY')
REDIRECT_URI = 'https://localhost:8888/callback'
AUTHORIZATION_BASE_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
SCOPE = 'user-library-read user-read-playback-state playlist-modify-public'

# Initialize Flask app
app = Flask(__name__)
app.secret_key =  b'\xc0\x99}\xce\xa9\xde$:\xcf\xce3\xb83~\x9a&\xb4\xc3V\x87\x96\x08\xc6\x80'
# Replace with a secure random value
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)


# Route for the home page
@app.route('/')
def home():
    # Create an OAuth2 session
    spotify = OAuth2Session(CLIENT_ID, scope=SCOPE, redirect_uri=REDIRECT_URI)
    authorization_url, state = spotify.authorization_url(AUTHORIZATION_BASE_URL)
    print(f"Generated state: {state}")  # Debug: Print the state

    # Store state in session for later use
    session['oauth_state'] = state
    print(f"Session after setting state: {session}")  # Debug: Print session data

    return redirect(authorization_url)

# Route for handling the callback from Spotify
@app.route('/callback')
def callback():
    print(f"Session at callback: {session}")  # Debug: Print session data

    # Debug: Check if oauth_state is in session
    if 'oauth_state' not in session:
        print("Error: 'oauth_state' not in session.")
        return "State not found in session.", 400
    
    print(f"Session state: {session['oauth_state']}")  # Debug: Print the session state
    # Create an OAuth2 session with the state stored in session
    spotify = OAuth2Session(CLIENT_ID, state=session['oauth_state'], redirect_uri=REDIRECT_URI)
    # Fetch the access token using the authorization response URL
    token = spotify.fetch_token(TOKEN_URL, client_secret=CLIENT_SECRET, authorization_response=request.url)
    # Store the token in session
    session['oauth_token'] = token

    return redirect(url_for('.profile'))
@app.route('/profile')
def profile():
    # Step 3: Use the access token to access user data.
    spotify = OAuth2Session(CLIENT_ID, token=session.get('oauth_token'))

    # Fetch the user's profile information
    response = spotify.get('https://api.spotify.com/v1/me')
    user_info = response.json()
    
    # Fetch the user's top tracks (example of accessing more data)
    top_tracks_response = spotify.get('https://api.spotify.com/v1/me/top/tracks')
    top_tracks = top_tracks_response.json()

    return f"User info: {user_info}<br><br>Top tracks: {top_tracks}"


# Run the Flask app
if __name__ == '__main__':
    app.run(port=8888, ssl_context=('cert.pem', 'key.pem'))

