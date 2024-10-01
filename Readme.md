# Project Name: Spotify OAuth App

## Overview
This project is a Flask-based web application that integrates with the Spotify API to allow users to authenticate via OAuth, view their Spotify profile, access their playlists, and track their recently played songs. The app is designed with a focus on user experience, providing a seamless and interactive interface using HTML, CSS, and JavaScript.

## Goal
The primary goal of this project is to analyze the user's listening patterns and create personalized playlists based on their listening activity.  The app runs continuously, collecting user listening data and generating weekly  playlist updates. the app is also capable of fetching and displaying the user's recently played tracks.

## Features
- **OAuth Authentication**: Users can securely log in to their Spotify account using the OAuth protocol.
- **Profile Viewing**: Displays the user's Spotify profile information, including their playlists.
- **Recently Played Tracks**: Fetches and stores the user's recently played tracks from Spotify, allowing them to view this data later.
- **Interactive UI**: The application includes responsive design elements, loaders, and dynamic content updates for a smooth user experience.
- **Playlist Creation and Updates**: Automatically generates and updates a personalized playlist based on the user's recent listening activity. Playlists are refreshed on a monthly basis.

## File Structure
```plaintext
.
├── .env                     # Environment variables
├── auth.py                  # Handles authentication and Spotify API interaction
├── db_operations.py         # Handles database interactions
├── __init__.py              # Initializes the Python package
├── templates/               # Folder for HTML templates
├── static/                  # Folder for static assets (CSS, JS, images)
│   ├── frontpage.css        # CSS for front page
│   ├── login.js             # JavaScript for login functionality
│   ├── logo.svg             # SVG logo file
│   ├── Profile.css          # CSS for profile page
│   ├── profile.js           # JavaScript for profile page
│   ├── script.js            # General JavaScript
│   ├── stats.css            # CSS for stats page
│   ├── styles.css           # Main CSS stylesheet
│   ├── toptrack.css         # CSS for top track section
│   ├── user-solid.svg       # SVG for user icon
│   └── welcome.css          # CSS for welcome page


```
## Setup Instructions
1. **Clone the repository**:
   ```bash
   git clone https://github.com/fumnanya12/Playlist.git
2. **Navigate to the project directory**:
   ```bash
   cd spotify-oauth-app
3. **Install dependencies**:
   ```bash
    pip install -r requirements.txt
4. **Set up environment variables**:
   
   Create a .env file in the root directory and add your Spotify API credentials:
     ```plaintext
     API_ID=your_spotify_client_id
     API_KEY=your_spotify_client_secret
     MONGODB_URI= your_mongodb_url_link

5. **Follow spotify Developer instruction**
   replace the SPOTIPY_REDIRECT_URI with  https://localhost:8888/callback 
   Also add it to your spotify dashbord
6. **Remove the (.) from from .db_operations**
   from .db_operations import store_recent_play, get_all_recent_plays,save_users_to_db,get_user_access_token,get_all_users,check_for_playlist,get_playlist_tracks,update_user_permissions,get_user_playlistid,delete_old_songs

   
7. **Run the application:**
   ```plaintext
      python auth.py 
  
  The application will be accessible at http://localhost:5000.

## Usage
1. Navigate to the home page and click on "Login with Spotify."
2. Authorize the app to access your Spotify account.
3. After successful login, you will be redirected to the profile page where you can view your playlists.
4. You can also generate and view a list of your recently played tracks.
5. You can provide permission for the app to listen to your actuvity and create a playlist weekly 
6. You can choose to stop giving permission 

## Dependencies
- **Flask**: Web framework used to build the application.
- **Requests**: Library used to make HTTP requests to the Spotify API.
- **Python-dotenv**: For loading environment variables from a `.env` file.
- **MongoDB**: Database used to store recently played tracks.

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.


## Acknowledgements
- Spotify API for providing the music data.
- Flask documentation for guidance on building web applications.

