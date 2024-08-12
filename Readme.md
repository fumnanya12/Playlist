# Project Name: Spotify OAuth App

## Overview
This project is a Flask-based web application that integrates with the Spotify API to allow users to authenticate via OAuth, view their Spotify profile, access their playlists, and track their recently played songs. The app is designed with a focus on user experience, providing a seamless and interactive interface using HTML, CSS, and JavaScript.

## Goal
The primary goal of this project is to analyze the user's listening patterns and create personalized playlists based on their listening activity. The project is still in the early stages of development and will be updated periodically as new features are added. Currently, the app is capable of fetching and displaying the user's recently played tracks.

## Features
- **OAuth Authentication**: Users can securely log in to their Spotify account using the OAuth protocol.
- **Profile Viewing**: Displays the user's Spotify profile information, including their playlists.
- **Recently Played Tracks**: Fetches and stores the user's recently played tracks from Spotify, allowing them to view this data later.
- **Interactive UI**: The application includes responsive design elements, loaders, and dynamic content updates for a smooth user experience.

## File Structure
- **`auth.py`**: The core of the application, handling routes for user authentication, fetching user data, and interacting with the Spotify API.
- **`db_operations.py`**: Contains functions for storing and retrieving recently played tracks from the database.
- **`styles.css`**: Defines the visual style of the profile page, including layout, colors, and animations.
- **`welcome.css`**: Styles the welcome page, focusing on user onboarding and login options.
- **`.env`**: (Not included) A file to store sensitive information like the Spotify API client ID, client secret, and other environment variables.

## Setup Instructions
1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/spotify-oauth-app.git
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
5. **Run the application:**
   ```plaintext
      python auth.py
  
  The application will be accessible at http://localhost:5000.

## Usage
1. Navigate to the home page and click on "Login with Spotify."
2. Authorize the app to access your Spotify account.
3. After successful login, you will be redirected to the profile page where you can view your playlists.
4. You can also generate and view a list of your recently played tracks.

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

