import os
import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build

def get_playlist_items(youtube, playlist_id, playlist_title):
    """
    Retrieves all video items from a specific playlist.
    """
    items = []
    next_page_token = None
    
    print(f"Fetching videos for playlist: {playlist_title} ({playlist_id})...")
    
    while True:
        request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()
        
        for item in response['items']:
            snippet = item['snippet']
            items.append({
                'playlist_id': playlist_id,
                'playlist_title': playlist_title,
                'video_id': snippet['resourceId']['videoId'],
                'video_title': snippet['title'],
                'position': item['snippet']['position']
            })
            
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
            
    return items

def main():
    load_dotenv()
    api_key = os.getenv("YOUTUBE_API_KEY")
    
    if not os.path.exists("playlists.csv"):
        print("Error: playlists.csv not found. Please run fetch_playlists.py first.")
        return

    youtube = build('youtube', 'v3', developerKey=api_key)
    playlists_df = pd.read_csv("playlists.csv")
    
    all_mapping = []
    
    for _, row in playlists_df.iterrows():
        items = get_playlist_items(youtube, row['playlist_id'], row['playlist_title'])
        all_mapping.extend(items)
        
    df = pd.DataFrame(all_mapping)
    output_file = "playlist_video_mapping.csv"
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\nSuccessfully saved mapping for {len(df)} items to {output_file}")

if __name__ == "__main__":
    main()
