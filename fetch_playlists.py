import os
import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build

def get_all_playlists(youtube, channel_id):
    """
    Retrieves all playlists for a given channel.
    """
    playlists = []
    next_page_token = None
    
    print(f"Fetching playlists for channel {channel_id}...")
    
    while True:
        request = youtube.playlists().list(
            part="snippet,contentDetails",
            channelId=channel_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()
        
        for item in response['items']:
            playlists.append({
                'playlist_id': item['id'],
                'playlist_title': item['snippet']['title'],
                'video_count': item['contentDetails']['itemCount']
            })
            
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
            
    return playlists

def main():
    load_dotenv()
    api_key = os.getenv("YOUTUBE_API_KEY")
    channel_id = os.getenv("TARGET_CHANNEL_ID")
    
    if not api_key or not channel_id:
        print("Error: YOUTUBE_API_KEY or TARGET_CHANNEL_ID missing in .env")
        return

    youtube = build('youtube', 'v3', developerKey=api_key)

    try:
        playlists = get_all_playlists(youtube, channel_id)
        df = pd.DataFrame(playlists)
        output_file = "playlists.csv"
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"Successfully saved {len(df)} playlists to {output_file}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
