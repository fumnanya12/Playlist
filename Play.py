import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Replace with your own Spotify Developer credentials
CLIENT_ID = '5e5791dfd3c2403186d74ead71ca4b7e'
CLIENT_SECRET = '7b98b90cfd8647b3b40dd009bd4e54d7'

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