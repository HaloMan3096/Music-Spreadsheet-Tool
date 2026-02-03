import spotipy
from spotipy.oauth2 import SpotifyOAuth
import config
import json
import os


def authenticate_spotify():
    """
    Authenticate with Spotify API and return a Spotipy client
    """
    print("🔑 Starting Spotify authentication...")

    # Check if we have saved tokens
    token_file = 'spotify_token.json'

    if os.path.exists(token_file):
        print("📁 Found existing token file")
        try:
            with open(token_file, 'r') as f:
                token_info = json.load(f)

            # Create auth manager with saved token
            sp_oauth = SpotifyOAuth(
                client_id=config.SPOTIFY_CLIENT_ID,
                client_secret=config.SPOTIFY_CLIENT_SECRET,
                redirect_uri=config.SPOTIFY_REDIRECT_URI,
                scope=' '.join(config.SPOTIFY_SCOPES)
            )

            # Check if token needs refresh
            if sp_oauth.is_token_expired(token_info):
                print("🔄 Token expired, refreshing...")
                token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
                # Save the new token
                with open(token_file, 'w') as f:
                    json.dump(token_info, f)

            # Create Spotipy client with token
            sp = spotipy.Spotify(auth=token_info['access_token'])
            print("✓ Authenticated with saved token")
            return sp

        except Exception as e:
            print(f"✗ Error with saved token: {e}")
            print("Starting fresh authentication...")
            os.remove(token_file)

    # Fresh authentication
    print("🌐 Opening browser for Spotify authentication...")
    print("If browser doesn't open, visit the URL shown below")

    try:
        sp_oauth = SpotifyOAuth(
            client_id=config.SPOTIFY_CLIENT_ID,
            client_secret=config.SPOTIFY_CLIENT_SECRET,
            redirect_uri=config.SPOTIFY_REDIRECT_URI,
            scope=' '.join(config.SPOTIFY_SCOPES),
            cache_path=token_file
        )

        # Get access token
        sp = spotipy.Spotify(auth_manager=sp_oauth)

        # Test the connection
        user = sp.current_user()
        print(f"✓ Successfully authenticated as: {user['display_name']}")
        print(f"✓ Email: {user['email']}")

        return sp

    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure your Client ID and Secret in config.py are correct")
        print("2. Ensure the Redirect URI matches exactly: http://localhost:8888/callback")
        print("3. Check that you've added this URI in your Spotify App settings")
        return None


def test_spotify_connection():
    """
    Test if we can successfully connect to Spotify API
    """
    sp = authenticate_spotify()

    if sp:
        print("\n🎧 Testing Spotify API connections...")

        # Test 1: Get user profile
        try:
            user = sp.current_user()
            print(f"✓ User Profile: {user['display_name']} ({user['id']})")
        except Exception as e:
            print(f"✗ Failed to get user profile: {e}")

        # Test 2: Get recently played tracks
        try:
            recent = sp.current_user_recently_played(limit=5)
            if recent['items']:
                print("✓ Recently Played Tracks:")
                for i, item in enumerate(recent['items'][:3]):
                    track = item['track']
                    print(f"  {i + 1}. {track['name']} - {track['artists'][0]['name']}")
            else:
                print("✓ No recently played tracks found")
        except Exception as e:
            print(f"✗ Failed to get recent tracks: {e}")

        # Test 3: Get top artists
        try:
            top_artists = sp.current_user_top_artists(limit=5)
            if top_artists['items']:
                print("✓ Top Artists:")
                for i, artist in enumerate(top_artists['items'][:3]):
                    print(f"  {i + 1}. {artist['name']}")
            else:
                print("✓ No top artists data yet")
        except Exception as e:
            print(f"✗ Failed to get top artists: {e}")

        return sp
    else:
        return None


if __name__ == "__main__":
    sp = test_spotify_connection()
    if sp:
        print("\n✅ Spotify API connection successful!")
        print("\nReady to fetch your Spotify data!")
    else:
        print("\n❌ Failed to connect to Spotify API")