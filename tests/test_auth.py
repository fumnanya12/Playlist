import unittest
from unittest.mock import patch, MagicMock
import spotify_auth_app.auth  # Import your program (auth.py) where delete_song_from_playlist is located

class TestDeleteSongFromPlaylist(unittest.TestCase):

    @patch('spotify_auth_app.auth.requests.delete')  # Mock the requests.delete function
    @patch('spotify_auth_app.auth.get_user_access_token')  # Mock get_user_access_token
    @patch('spotify_auth_app.auth.get_access_token')  # Mock get_access_token
    @patch('spotify_auth_app.auth.get_user_playlistid')  # Mock get_user_playlistid
    @patch('spotify_auth_app.auth.delete_old_songs')  # Mock delete_old_songs
    def test_delete_song_from_playlist_successful(self, mock_delete_old_songs, mock_get_user_playlistid, mock_get_access_token, mock_get_user_access_token, mock_requests_delete):
        # Mock return values for access token and user permissions
        mock_get_access_token.return_value = 'valid_access_token'
        mock_get_user_access_token.return_value = ('user_access_token', 'user_refresh_token', 'token_expiry', 'yes', 'user_email')
        mock_get_user_playlistid.return_value = 'playlist123'
        
        # Mock return value of delete_old_songs (list of songs to delete)
        mock_delete_old_songs.return_value = [
            {"_id": {"song_name": "Song 1", "song_id": "123"}},
            {"_id": {"song_name": "Song 2", "song_id": "456"}}
        ]
        
        # Mock requests.delete response
        mock_requests_delete.return_value.status_code = 200

        # Call the function
        result = spotify_auth_app.auth.delete_song_from_playlist('test_user')

        # Ensure delete_old_songs is called
        mock_delete_old_songs.assert_called_once_with('test_user')
        
        # Ensure requests.delete is called for each song
        expected_url = 'https://api.spotify.com/v1/playlists/playlist123/tracks'
        mock_requests_delete.assert_any_call(expected_url, headers={'Authorization': 'Bearer valid_access_token'}, json={'tracks': [{'uri': 'spotify:track:123'}]})
        mock_requests_delete.assert_any_call(expected_url, headers={'Authorization': 'Bearer valid_access_token'}, json={'tracks': [{'uri': 'spotify:track:456'}]})
        
        # Check that the function runs successfully without errors
        self.assertIsNone(result)

    @patch('spotify_auth_app.auth.get_user_playlistid')  # Mock get_user_playlistid
    @patch('spotify_auth_app.auth.get_user_access_token')  # Mock get_user_access_token
    @patch('spotify_auth_app.auth.get_access_token')  # Mock get_access_token
    @patch('spotify_auth_app.auth.delete_old_songs')  # Mock delete_old_songs
    def test_delete_song_from_playlist_no_songs(self, mock_delete_old_songs, mock_get_access_token, mock_get_user_access_token, mock_get_user_playlistid):
        # Mock access token
        mock_get_access_token.return_value = 'valid_access_token'
        mock_get_user_access_token.return_value = ('user_access_token', 'user_refresh_token', 'token_expiry', 'yes', 'user_email')
        mock_get_user_playlistid.return_value = 'playlist123'



        # Mock delete_old_songs to return None (no songs to delete)
        mock_delete_old_songs.return_value = None

        # Call the function
        result = spotify_auth_app.auth.delete_song_from_playlist('test_user')

        # Ensure delete_old_songs is called
        mock_delete_old_songs.assert_called_once_with('test_user')

        # Ensure the function exits early when no songs are found
        self.assertIsNone(result)

    @patch('spotify_auth_app.auth.get_user_access_token')  # Mock get_user_access_token
    @patch('spotify_auth_app.auth.get_access_token')  # Mock get_access_token
    def test_delete_song_from_playlist_no_access_token(self, mock_get_access_token, mock_get_user_access_token):
        # Mock no access token
        mock_get_access_token.return_value = None
        mock_get_user_access_token.return_value = ('user_access_token', 'user_refresh_token', 'token_expiry', 'yes', 'user_email')

        # Call the function
        result = spotify_auth_app.auth.delete_song_from_playlist('test_user')

        # Ensure the function exits early when no access token is provided
        self.assertIsNone(result)
        mock_get_access_token.assert_called_once_with('test_user')


if __name__ == '__main__':
    unittest.main()
