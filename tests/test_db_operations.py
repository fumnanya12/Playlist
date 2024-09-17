import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime,timedelta
import pytz
import spotify_auth_app.db_operations as db_operations  # Update the import to your correct module path

class TestDbOperations(unittest.TestCase):

    @patch('spotify_auth_app.db_operations.db')  # Mock the db
    def test_store_recent_play(self, mock_db):
        # Mock collection
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection

        # Sample input
        song_name = "Test Song"
        song_id = "123"
        play_time = "2024-08-08T12:00:00Z"
        user_name = "test_user"
        artist_name = "Test Artist"

        # Test no existing play
        mock_collection.find_one.return_value = None

        # Call the function
        db_operations.store_recent_play(song_name, song_id, play_time, user_name, artist_name)

        # Ensure the insert_one method is called
        mock_collection.insert_one.assert_called_once()

    @patch('spotify_auth_app.db_operations.db')  # Mock the db
    def test_save_users_to_db(self, mock_db):
        # Mock collection
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection  # Make sure this mock returns the correct collection

        # Sample input
        user_id = "test_user"
        access_token = "token123"
        refresh_token = "refresh123"
        token_expiry = datetime.now()
        email = "test@example.com"
        permission = "yes"

        # Call the function
        db_operations.save_users_to_db(user_id, access_token, refresh_token, token_expiry, email, permission)

        # Ensure the update_one method is called with the correct data
        mock_collection.update_one.assert_called_once_with(
            {"$or": [{"user_id": user_id}, {"email": email}]},
            {
                "$set": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_expiry": token_expiry,
                }
            },
            upsert=True
        )

    @patch('spotify_auth_app.db_operations.db')  # Mock the db
    def test_store_recent_play2(self, mock_db):
        # Mock collection
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection

        # Sample input
        song_name = "Test Song"
        song_id = "12345"
        play_time = "2024-08-08T12:00:00Z"
        user_name = "test_user"
        artist_name = "Test Artist"

        # Expected datetime conversion
        play_time_obj = datetime.fromisoformat(play_time[:-1])
        play_time_utc = pytz.utc.localize(play_time_obj)
        play_time_winnipeg = play_time_utc.astimezone(pytz.timezone('America/Winnipeg'))
        play_date = play_time_winnipeg
        play_time_only = play_time_winnipeg.time().isoformat()

        # Mock the find_one result to simulate no existing record
        mock_collection.find_one.return_value = None

        # Mock the count_documents method to simulate the database size before and after insertion
        mock_collection.count_documents.side_effect = [0, 1]  # Simulate size before and after insertion

        # Call count_documents to get the initial size
        initial_size = mock_collection.count_documents({})

        # Call the function (which inserts the record)
        db_operations.store_recent_play(song_name, song_id, play_time, user_name, artist_name)

        # Ensure the find_one method is called with the correct filter
        mock_collection.find_one.assert_called_once_with({
            "song_name": song_name,
            "song_id": song_id,
            "artist_name": artist_name,
            "play_date": play_date,
            "play_time": play_time_only
        })

        # Ensure insert_one is called since no existing record was found
        mock_collection.insert_one.assert_called_once_with({
            "song_name": song_name,
            "song_id": song_id,
            "artist_name": artist_name,
            "play_date": play_date,
            "play_time": play_time_only
        })

        # Call count_documents to get the final size after insertion
        final_size = mock_collection.count_documents({})

        # Verify that the initial size is 0 and the final size is 1
        self.assertEqual(initial_size, 0)  # Before insertion, the size is 0
        self.assertEqual(final_size, 1)    # After insertion, the size is 1
    @patch('spotify_auth_app.db_operations.db') 
    def test_get_user_access_token(self, mock_db):
         # Mock collection
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
         # Sample input
        user_id = "test_user"
        access_token = "token123"
        refresh_token = "refresh123"
        token_expiry = datetime.now()
        email = "test@example.com"
        permission = "yes"
        mock_collection.find_one.return_value = (
            {
                'user_id': user_id,
            'email': email,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_expiry': token_expiry,
            'permissions': permission
            }
        )

        # Call the function
        result = db_operations.get_user_access_token(user_id)
        
        mock_collection.find_one.assert_called_once_with({'user_id': user_id})


        # Verify the result
        self.assertEqual(result, (access_token,refresh_token,token_expiry,permission,email))
    @patch('spotify_auth_app.db_operations.db') 
    def test_get_user_playlistid(self, mock_db):
        # Mock collection
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
         # Sample input
        user_id = "test_user"
        playlist_id = "test_playlist"
        mock_collection.find_one.return_value = (
            {
                'user_id': user_id,
                'playlist_id': playlist_id
            }
        )

        # Call the function
        result = db_operations.get_user_playlistid(user_id)
        
        mock_collection.find_one.assert_called_once_with({'user_id': user_id})

        # Verify the result
        self.assertEqual(result, playlist_id)
    @patch('spotify_auth_app.db_operations.db') 
    def test_update_user_permissions(self, mock_db):
        # Mock collection
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
         # Sample input
        user_id = "test_user"
        permission = "yes"
        mock_collection.find_one.return_value = (
            {
                'user_id': user_id
            }
        )

        # Call the function
        db_operations.update_user_permissions(user_id,permission)
        
        mock_collection.find_one.assert_called_once_with({'user_id': user_id})
        mock_collection.update_one.assert_called_once_with({'user_id': user_id}, {'$set': {'permissions': permission}})
    @patch('spotify_auth_app.db_operations.db')
    def test_get_all_users(self, mock_db):
        # Mock collection
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection

        mock_collection.find.return_value = [
            {'user_id': 'user1'},
            {'user_id': 'user2'},   
        ]
        result = db_operations.get_all_users()
        mock_collection.find.assert_called_once()
        self.assertEqual(len(result), 2)
        self.assertEqual(result, [{'user_id': 'user1'}, {'user_id': 'user2'}])
    @patch('spotify_auth_app.db_operations.db')
    def test_add_artist_name(self, mock_db):
        # Mock collection   
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        
        # Sample input
        user_id = "test_user"
        artist_name="test_artist"
        song_id="test_song"

        # Mock the result of update_one
        mock_update_result = MagicMock()
        mock_update_result.matched_count = 1  # Simulate that one document was matched

        # Set return value of update_one to the mock result
        mock_collection.update_one.return_value = mock_update_result

        db_operations.add_artist_name(song_id,artist_name,user_id)
        new_data = {"artist_name": artist_name}
        mock_collection.update_one.assert_called_once_with({'song_id': song_id}, {'$set': new_data})    
    @patch('spotify_auth_app.db_operations.db')  # Mock the db
    def test_check_for_playlist_permission_yes_playlist_exists(self, mock_db):
        # Sample inputs
        user_name = "test_user"
        playlist_id = "playlist123"
        playlistname = user_name + "_playlist"

        # Mocking the users collection and playlist collection
        mock_user_collection = MagicMock()
        mock_playlist_collection = MagicMock()
        mock_db.__getitem__.side_effect = lambda name: mock_user_collection if name == 'users' else mock_playlist_collection

        # Mocking the current user data
        mock_user_collection.find_one.return_value = {
            'user_id': user_name,
            'permissions': 'yes'
        }

        # Mocking the playlist already existing
        mock_playlist_collection.find_one.return_value = {
            'playlist_id': playlist_id
        }

        # Call the function
        db_operations.check_for_playlist(user_name, playlist_id)

        # Ensure the user's find_one was called
        mock_user_collection.find_one.assert_called_once_with({'user_id': user_name})
        
        # Ensure the playlist's find_one was called
        mock_playlist_collection.find_one.assert_called_once_with({'playlist_id': playlist_id})

    @patch('spotify_auth_app.db_operations.db')  # Mock the db
    def test_check_for_playlist_permission_yes_playlist_does_not_exist(self, mock_db):
        # Sample inputs
        user_name = "test_user"
        playlist_id = "playlist123"
        playlistname = user_name + "_playlist"

        # Mocking the users collection and playlist collection
        mock_user_collection = MagicMock()
        mock_playlist_collection = MagicMock()
        mock_db.__getitem__.side_effect = lambda name: mock_user_collection if name == 'users' else mock_playlist_collection

        # Mocking the current user data
        mock_user_collection.find_one.return_value = {
            'user_id': user_name,
            'permissions': 'yes'
        }

        # Mocking that the playlist does not exist
        mock_playlist_collection.find_one.return_value = None

        # Mocking update_one result
        mock_update_result = MagicMock()
        mock_update_result.matched_count = 1
        mock_user_collection.update_one.return_value = mock_update_result

        # Call the function
        db_operations.check_for_playlist(user_name, playlist_id)

        # Ensure the user's find_one was called
        mock_user_collection.find_one.assert_called_once_with({'user_id': user_name})
        
        # Ensure the playlist's find_one was called
        mock_playlist_collection.find_one.assert_called_once_with({'playlist_id': playlist_id})

        # Ensure update_one was called to update the user's document
        mock_user_collection.update_one.assert_called_once_with(
            {"user_id": user_name},
            {"$set": {"playlist_id": playlist_id}}
        )

    @patch('spotify_auth_app.db_operations.db')  # Mock the db
    def test_check_for_playlist_permission_no(self, mock_db):
        # Sample inputs
        user_name = "test_user"
        playlist_id = "playlist123"

        # Mocking the users collection
        mock_user_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_user_collection

        # Mocking the current user data with 'no' permissions
        mock_user_collection.find_one.return_value = {
            'user_id': user_name,
            'permissions': 'no'
        }

        # Call the function
        db_operations.check_for_playlist(user_name, playlist_id)

        # Ensure the user's find_one was called
        mock_user_collection.find_one.assert_called_once_with({'user_id': user_name})

        # Ensure that playlist find_one was never called because permissions are 'no'
        mock_db.__getitem__.assert_called_once_with('users')
        mock_user_collection.find_one.assert_called_once_with({'user_id': user_name})
        self.assertEqual(mock_db.__getitem__.call_count, 1)  # Verify no further collections are accesse
    @patch('spotify_auth_app.db_operations.addsong_to_playlist')  # Mock the addsong_to_playlist function
    @patch('spotify_auth_app.db_operations.db')  # Mock the db
    def test_get_playlist_tracks_successful(self, mock_db, mock_addsong_to_playlist):
        # Sample inputs
        user_name = "test_user"
        playlist_id = "playlist123"
         # Fixed current datetime for test consistency
        fixed_now = datetime(2024, 9, 17, 12, 4, 21)
        # Mock plays_collection
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        
        # Simulate the aggregation results from MongoDB
        mock_collection.aggregate.return_value = iter([
            {"_id": {"song_name": "Song1", "song_id": "123"}, "play_count": 5},
            {"_id": {"song_name": "Song2", "song_id": "456"}, "play_count": 6}
        ])

        # Mock add song to playlist returning True
        mock_addsong_to_playlist.side_effect = [True, True]

        # Call the function with a mocked datetime
        with patch('spotify_auth_app.db_operations.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_now  # Fix datetime.now() for consistency
            result = db_operations.get_playlist_tracks(user_name, playlist_id)
        # Check if aggregation was performed correctly
         # Check how many times aggregate was called
        aggregate_call_count = mock_collection.aggregate.call_count
        print(f"Aggregate call count: {aggregate_call_count}")

        # Ensure aggregate was called only once on the collection
        self.assertEqual(aggregate_call_count, 1, "Aggregate should be called only once.")

        # Check if add songs to playlist was called for each song
        mock_addsong_to_playlist.assert_any_call(user_name, playlist_id, {"_id": {"song_name": "Song1", "song_id": "123"}, "play_count": 5}, fixed_now)
        mock_addsong_to_playlist.assert_any_call(user_name, playlist_id, {"_id": {"song_name": "Song2", "song_id": "456"}, "play_count": 6}, fixed_now)

        # Ensure that the result contains the expected songs
        self.assertEqual(len(result), 2)

    @patch('spotify_auth_app.db_operations.addsong_to_playlist')  # Mock the addsong_to_playlist function
    @patch('spotify_auth_app.db_operations.db')  # Mock the db
    def test_get_playlist_tracks_no_songs_found(self, mock_db, mock_addsong_to_playlist):
        # Sample inputs
        user_name = "test_user"
        playlist_id = "playlist123"
        
        # Mock plays_collection
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        
        # Simulate no aggregation results (empty list)
        mock_collection.aggregate.return_value = iter([])

        # Call the function
        result = db_operations.get_playlist_tracks(user_name, playlist_id)

        # Check if aggregation was performed correctly
        mock_collection.aggregate.assert_called_once()

        # Ensure no songs were added to the playlist
        mock_addsong_to_playlist.assert_not_called()

        # Ensure that the result is an empty list
        self.assertEqual(result, [])

    @patch('spotify_auth_app.db_operations.addsong_to_playlist')  # Mock the addsong_to_playlist function
    @patch('spotify_auth_app.db_operations.db')  # Mock the db
    def test_get_playlist_tracks_collection_not_found(self, mock_db, mock_addsong_to_playlist):
        # Sample inputs
        user_name = "test_user"
        playlist_id = "playlist123"
        
        # Simulate collection not found
        mock_db.__getitem__.return_value = None

        # Expect the function to raise an Exception due to missing collection
        with self.assertRaises(Exception):
            db_operations.get_playlist_tracks(user_name, playlist_id)

    @patch('spotify_auth_app.db_operations.db')  # Mock the db
    def test_delete_old_songs_successful(self, mock_db):
        # Sample inputs
        user_name = "test_user"
        playlist_name = user_name + "_playlist"

        # Mock playlist collection
        mock_playlist_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_playlist_collection

        # Fixed current datetime for test consistency
        fixed_now = datetime(2024, 9, 15)
        one_month_ago = fixed_now - timedelta(days=30)

        # Mock the aggregation result
        mock_playlist_collection.aggregate.return_value = iter([
            {"_id": {"song_name": "Song 1", "song_id": "123"}},
            {"_id": {"song_name": "Song 2", "song_id": "456"}},
        ])
        # Mock `find_one` to simulate that the items do not exist after deletion
        mock_playlist_collection.find_one.side_effect = [None, None]
        # Call the function
        with patch('spotify_auth_app.db_operations.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_now  # Fix datetime.now() for consistency
            result = db_operations.delete_old_songs(user_name)

        # Check that the aggregation pipeline was called with the correct pipeline
        expected_pipeline = [
            {"$match": {"play_date": {"$gte": one_month_ago}}},
            {"$group": {"_id": {"song_name": "$song_name", "song_id": "$song_id"}}}
        ]
        mock_playlist_collection.aggregate.assert_called_once_with(expected_pipeline)
         # Mock `find_one` to simulate that the items do not exist after deletion
        # Ensure delete_one was called for each song in the results
        mock_playlist_collection.delete_one.assert_any_call({'Song_id': '123'})
        mock_playlist_collection.delete_one.assert_any_call({'Song_id': '456'})
        
        
        self.assertIsNone(mock_playlist_collection.find_one({'Song_id': '123'}))
        self.assertIsNone(mock_playlist_collection.find_one({'Song_id': '456'}))

        # Verify the result contains the expected songs
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['_id']['song_name'], 'Song 1')
        self.assertEqual(result[1]['_id']['song_name'], 'Song 2')
    @patch('spotify_auth_app.db_operations.db')  # Mock the db
    def test_delete_old_songs_no_songs_found(self, mock_db):
        # Sample inputs
        user_name = "test_user"
        playlist_name = user_name + "_playlist"

        # Mock playlist collection
        mock_playlist_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_playlist_collection

        # Simulate no results from aggregation
        mock_playlist_collection.aggregate.return_value = iter([])

        # Call the function
        result = db_operations.delete_old_songs(user_name)

        # Check that the aggregation was called
        mock_playlist_collection.aggregate.assert_called_once()

        # Ensure delete_one was never called since no songs were found
        mock_playlist_collection.delete_one.assert_not_called()

        # Ensure the result is an empty list
        self.assertEqual(result, [])

    @patch('spotify_auth_app.db_operations.db')  # Mock the db
    def test_delete_old_songs_collection_not_found(self, mock_db):
        # Sample inputs
        user_name = "test_user"
        playlist_name = user_name + "_playlist"

        # Simulate playlist collection not found
        mock_db.__getitem__.return_value = None

        # Expect an exception to be raised
        with self.assertRaises(Exception) as context:
            db_operations.delete_old_songs(user_name)

        self.assertTrue("Collection for user test_user does not exist." in str(context.exception))

    @patch('spotify_auth_app.db_operations.db')  # Mock the db
    def test_addsong_to_playlist_song_already_exists(self, mock_db):
        # Sample inputs
        user_name = "test_user"
        playlist_id = "playlist123"
        song_details = {
            '_id': {'song_name': 'Song 1', 'song_id': '123'}
        }
        date_added = datetime(2024, 9, 15)
        
        # Mock playlist collection
        mock_playlist_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_playlist_collection

        # Mock find_one to return an existing song (song already in the playlist)
        mock_playlist_collection.find_one.return_value = {
            'Song_id': '123',
            'Song_name': 'Song 1'
        }

        # Call the function
        result = db_operations.addsong_to_playlist(user_name, playlist_id, song_details, date_added)

        # Ensure find_one was called with the correct query
        mock_playlist_collection.find_one.assert_called_once_with({
            '$or': [{'Song_id': '123'}, {'Song_name': 'Song 1'}]
        })

        # Ensure update_one was called to update the 'Date added' field
        mock_playlist_collection.update_one.assert_called_once_with(
            {'Song_id': '123'}, 
            {"$set": {"Date added": date_added}}
        )

        # Check that the result indicates the song already existed (update is False)
        self.assertFalse(result)

    @patch('spotify_auth_app.db_operations.db')  # Mock the db
    def test_addsong_to_playlist_song_does_not_exist(self, mock_db):
        # Sample inputs
        user_name = "test_user"
        playlist_id = "playlist123"
        song_details = {
            '_id': {'song_name': 'Song 1', 'song_id': '123'}
        }
        date_added = datetime(2024, 9, 15)
        
        # Mock playlist collection
        mock_playlist_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_playlist_collection

        # Mock find_one to return None (song does not exist in the playlist)
        mock_playlist_collection.find_one.return_value = None

        # Call the function
        result = db_operations.addsong_to_playlist(user_name, playlist_id, song_details, date_added)

        # Ensure find_one was called with the correct query
        mock_playlist_collection.find_one.assert_called_once_with({
            '$or': [{'Song_id': '123'}, {'Song_name': 'Song 1'}]
        })

        # Ensure insert_one was called to add the new song
        mock_playlist_collection.insert_one.assert_called_once_with({
            'Playlist_id': playlist_id,
            'Song_id': '123',
            'Song_name': 'Song 1',
            'Date added': date_added
        })

        # Check that the result indicates the song was added (update is True)
        self.assertTrue(result)
if __name__ == '__main__':
    unittest.main()
