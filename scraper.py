import os
import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build

def get_uploads_playlist_id(youtube, channel_id):
    """
    Retrieves the ID of the 'uploads' playlist for a given channel.
    """
    request = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    )
    response = request.execute()
    
    if not response['items']:
        raise ValueError(f"Channel ID {channel_id} not found.")
        
    return response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

def get_all_video_ids_from_playlist(youtube, playlist_id):
    """
    Retrieves all video IDs from a specific playlist.
    """
    video_ids = []
    next_page_token = None
    
    print(f"Fetching video IDs from playlist {playlist_id}...")
    
    while True:
        request = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()
        
        for item in response['items']:
            video_ids.append(item['contentDetails']['videoId'])
            
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
            
    print(f"Found {len(video_ids)} videos.")
    return video_ids

def get_video_details(youtube, video_ids):
    """
    Retrieves detailed metadata for a list of video IDs.
    Batches requests in groups of 50.
    """
    video_data = []
    
    # Process in batches of 50
    for i in range(0, len(video_ids), 50):
        batch_ids = video_ids[i:i+50]
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=','.join(batch_ids)
        )
        response = request.execute()
        
        for item in response['items']:
            snippet = item['snippet']
            statistics = item['statistics']
            content_details = item['contentDetails']
            
            video_info = {
                'video_id': item['id'],
                'title': snippet['title'],
                'url': f"https://www.youtube.com/watch?v={item['id']}",
                'published_at': snippet['publishedAt'],
                'view_count': statistics.get('viewCount', 0),
                'like_count': statistics.get('likeCount', 0),
                'comment_count': statistics.get('commentCount', 0),
                'duration': content_details['duration'],
                'tags': ','.join(snippet.get('tags', []))
            }
            video_data.append(video_info)
            
    return video_data

def main():
    # 1. Load Environment Variables
    load_dotenv()
    api_key = os.getenv("YOUTUBE_API_KEY")
    
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        print("Error: Please set a valid YOUTUBE_API_KEY in the .env file.")
        return

    # 2. Initialize API Service
    youtube = build('youtube', 'v3', developerKey=api_key)
    target_channel_id = os.getenv("TARGET_CHANNEL_ID")

    if not target_channel_id:
        print("Error: Please set TARGET_CHANNEL_ID in the .env file.")
        return

    try:
        # 3. Get Uploads Playlist ID
        uploads_playlist_id = get_uploads_playlist_id(youtube, target_channel_id)
        
        # 4. Get All Video IDs
        all_video_ids = get_all_video_ids_from_playlist(youtube, uploads_playlist_id)
        
        # 5. Get Detailed Metadata
        print("Fetching detailed metadata...")
        video_details = get_video_details(youtube, all_video_ids)
        
        # 6. Save to CSV
        df = pd.DataFrame(video_details)
        output_filename = "channel_videos_metadata.csv"
        df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        print(f"Successfully saved metadata for {len(df)} videos to {output_filename}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
