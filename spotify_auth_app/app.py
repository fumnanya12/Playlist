# app.py

from flask import Flask, redirect, request, session, url_for
from requests_oauthlib import OAuth2Session
import os
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()


# Configuration
CLIENT_ID = os.getenv('API_ID')
CLIENT_SECRET = os.getenv('API_KEY')
REDIRECT_URI = 'http://localhost:8888/callback'
AUTHORIZATION_BASE_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
SCOPE = 'user-library-read user-read-playback-state playlist-modify-public'

# Initialize Flask app
app = Flask(__name__)
app.secret_key =  os.urandom(24)  # Replace with a secure random value

# Route for the home page
@app.route('/')
def home():
    # Create an OAuth2 session
    spotify = OAuth2Session(CLIENT_ID, scope=SCOPE, redirect_uri=REDIRECT_URI)
    authorization_url, state = spotify.authorization_url(AUTHORIZATION_BASE_URL)

    # Store state in session for later use
    session['oauth_state'] = state
    return redirect(authorization_url)

# Route for handling the callback from Spotify
@app.route('/callback')
def callback():
    # Create an OAuth2 session with the state stored in session
    spotify = OAuth2Session(CLIENT_ID, state=session['oauth_state'], redirect_uri=REDIRECT_URI)
    # Fetch the access token using the authorization response URL
    token = spotify.fetch_token(TOKEN_URL, client_secret=CLIENT_SECRET, authorization_response=request.url)
    # Store the token in session
    session['oauth_token'] = token

    return 'Authentication successful!'

# Run the Flask app
if __name__ == '__main__':
    app.run(port=8888)
