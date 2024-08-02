import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from dotenv import load_dotenv

# Load environment variables fclearom .env file
load_dotenv()

# Replace with your own Spotify Developer credentials
CLIENT_ID = os.getenv('API_ID')
CLIENT_SECRET = os.getenv('API_KEY')

# Authentication - without user
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=CLIENT_ID,
                                                           client_secret=CLIENT_SECRET))

# Example function to get an artist's top tracks
def get_artist_top_tracks(artist_name):
    results = sp.search(q='artist:' + artist_name, type='artist')
    items = results['artists']['items']
    if len(items) > 0:
        artist = items[0]
        artist_id = artist['id']
        top_tracks = sp.artist_top_tracks(artist_id)
        for track in top_tracks['tracks']:
            print('Track: ', track['name'])


# Example usage
get_artist_top_tracks('Gbengahimself')