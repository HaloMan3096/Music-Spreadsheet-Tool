import spotipy
from spotipy.oauth2 import SpotifyOAuth
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import config
from datetime import datetime
import json
import time

def get_google_sheet():
    """Connect to Google Sheets"""
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            config.GOOGLE_SHEETS_CREDENTIALS,
            config.SCOPES
        )
        client = gspread.authorize(creds)
        spreadsheet = client.open(config.SHEET_NAME)
        worksheet = spreadsheet.sheet1

        # Set up headers if sheet is empty
        if not worksheet.get('A1'):
            headers = [
                ["Timestamp", "Type", "Track Name", "Artist(s)", "Album", "Duration (ms)",
                 "Popularity", "Played At", "Context"]
            ]
            worksheet.append_rows(headers)
        return worksheet
    except Exception as e:
        print(f"Google Sheets error: {e}")
        return None


def get_spotify_client():
    """Authenticate with Spotify"""
    try:
        sp_oauth = SpotifyOAuth(
            client_id=config.SPOTIFY_CLIENT_ID,
            client_secret=config.SPOTIFY_CLIENT_SECRET,
            redirect_uri=config.SPOTIFY_REDIRECT_URI,
            scope=' '.join(config.SPOTIFY_SCOPES),
            cache_path='spotify_token.json'
        )
        sp = spotipy.Spotify(auth_manager=sp_oauth)
        return sp
    except Exception as e:
        print(f"Spotify authentication error: {e}")
        return None


def get_recently_played(sp, limit=50):
    """Get recently played tracks"""
    try:
        results = sp.current_user_recently_played(limit=limit)
        tracks_data = []

        for item in results['items']:
            track = item['track']
            played_at = item.get('played_at', '')

            # Format played_at timestamp
            if played_at:
                dt = datetime.strptime(played_at, '%Y-%m-%dT%H:%M:%S.%fZ')
                played_at_formatted = dt.strftime('%Y-%m-%d %H:%M:%S')
            else:
                played_at_formatted = ''

            # Get all artist names
            artists = ', '.join([artist['name'] for artist in track['artists']])

            tracks_data.append({
                'type': 'recent',
                'track_name': track['name'],
                'artists': artists,
                'album': track['album']['name'],
                'duration_ms': track['duration_ms'],
                'popularity': track['popularity'],
                'played_at': played_at_formatted,
                'context': item['context']['type'] if item['context'] else 'Unknown'
            })

        return tracks_data
    except Exception as e:
        print(f"Error fetching recently played: {e}")
        return []


def get_top_tracks(sp, limit=20, time_range='medium_term'):
    """Get top tracks (short_term=last 4 weeks, medium_term=last 6 months, long_term=all time)"""
    try:
        results = sp.current_user_top_tracks(limit=limit, time_range=time_range)
        tracks_data = []

        for track in results['items']:
            # Get all artist names
            artists = ', '.join([artist['name'] for artist in track['artists']])

            tracks_data.append({
                'type': f'top_{time_range}',
                'track_name': track['name'],
                'artists': artists,
                'album': track['album']['name'],
                'duration_ms': track['duration_ms'],
                'popularity': track['popularity'],
                'played_at': '',  # Top tracks don't have played_at
                'context': 'top_tracks'
            })

        return tracks_data
    except Exception as e:
        print(f"Error fetching top tracks: {e}")
        return []


def get_top_artists(sp, limit=20, time_range='medium_term'):
    """Get top artists"""
    try:
        results = sp.current_user_top_artists(limit=limit, time_range=time_range)
        artists_data = []

        for artist in results['items']:
            artists_data.append({
                'type': f'artist_{time_range}',
                'track_name': '',  # Not applicable for artists
                'artists': artist['name'],
                'album': '',  # Not applicable
                'duration_ms': '',
                'popularity': artist['popularity'],
                'played_at': '',
                'context': 'top_artists',
                'genres': ', '.join(artist['genres'][:3])  # First 3 genres
            })

        print(f"Found {len(artists_data)} top artists")
        return artists_data
    except Exception as e:
        print(f"✗ Error fetching top artists: {e}")
        return []


def export_to_sheets(worksheet, data):
    """Export data to Google Sheets"""
    if not data:
        print("No data to export")
        return

    # Convert data to rows for Google Sheets
    rows = []
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for item in data:
        row = [
            timestamp,
            item.get('type', ''),
            item.get('track_name', ''),
            item.get('artists', ''),
            item.get('album', ''),
            item.get('duration_ms', ''),
            item.get('popularity', ''),
            item.get('played_at', ''),
            item.get('context', '')
        ]
        rows.append(row)

    # Append rows in batches to avoid rate limits
    batch_size = 50
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        try:
            worksheet.append_rows(batch)
            time.sleep(1)  # Avoid rate limiting
        except Exception as e:
            print(f"✗ Error adding batch: {e}")

def main():
    """Main function to run the Spotify to Sheets export"""

    # Step 1: Connect to Spotify
    sp = get_spotify_client()
    if not sp:
        return

    # Step 2: Connect to Google Sheets
    worksheet = get_google_sheet()
    if not worksheet:
        return

    # Step 3: Fetch data from Spotify
    # Get recently played tracks
    recent_tracks = get_recently_played(sp, limit=50)

    # Get top tracks (different time ranges)
    top_tracks_short = get_top_tracks(sp, limit=20, time_range='short_term')
    top_tracks_medium = get_top_tracks(sp, limit=20, time_range='medium_term')

    # Get top artists
    top_artists = get_top_artists(sp, limit=20, time_range='medium_term')

    # Combine all data
    all_data = recent_tracks + top_tracks_short + top_tracks_medium + top_artists

    # Step 4: Export to Google Sheets
    if all_data:
        export_to_sheets(worksheet, all_data)

        # Show summary
        print("\n📈 Data Summary:")
        print(f"  Recently Played: {len(recent_tracks)} tracks")
        print(f"  Top Tracks (4 weeks): {len(top_tracks_short)} tracks")
        print(f"  Top Tracks (6 months): {len(top_tracks_medium)} tracks")
        print(f"  Top Artists: {len(top_artists)} artists")
        print(f"  Total exported: {len(all_data)} rows")
    else:
        print("No data fetched from Spotify")

if __name__ == "__main__":
    main()