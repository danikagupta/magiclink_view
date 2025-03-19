"""Google API integration for YouTube transcript retrieval.

This module handles authentication with Google APIs and provides functionality
to fetch and parse YouTube video transcripts.
"""

import streamlit as st
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from typing import List, Dict, Union
import googleapiclient.discovery
from pathlib import Path

def get_google_creds(credential_file_path: str) -> Credentials:
    """Get or create Google API credentials.

    Args:
        credential_file_path: Path to the credentials JSON file

    Returns:
        Valid Google API credentials object
    """
    filepath = Path(credential_file_path)
    
    # Create credentials file if it doesn't exist
    if not filepath.exists():
        print(f"Creating credentials file: {credential_file_path}")
        # Parse scopes from string to proper JSON array
        scopes = json.loads(st.secrets['scopes'])
        
        credentials_data = {
            "refresh_token": st.secrets['refresh_token'],
            "token_uri": st.secrets['token_uri'],
            "client_id": st.secrets['client_id'],
            "client_secret": st.secrets['client_secret'],
            "scopes": scopes
        }
        
        content = json.dumps(credentials_data, indent=2)
        filepath.write_text(content)
    else:
        print(f"Using existing credentials from: {credential_file_path}")

    # Load and validate credentials
    credentials = Credentials.from_authorized_user_file(credential_file_path)
    if not credentials.valid and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    return credentials

def get_transcript(video_id: str) -> List[str]:
    """Fetch and parse the transcript for a YouTube video.

    Args:
        video_id: YouTube video ID to fetch transcript for

    Returns:
        List of transcript segments with timestamps

    Raises:
        Exception: If no English transcript is available
    """
    # Initialize YouTube API client
    API_SERVICE_NAME = "youtube"
    API_VERSION = "v3"
    AUTH_FILE = "my2credentials.json"

    credentials = get_google_creds(AUTH_FILE)
    youtube_client = googleapiclient.discovery.build(
        API_SERVICE_NAME, 
        API_VERSION, 
        credentials=credentials
    )

    # Get available captions
    captions_response = youtube_client.captions().list(
        part="id,snippet", 
        videoId=video_id
    ).execute()

    # Find English caption ID
    caption_id = None
    for item in captions_response.get("items", []):
        if item["snippet"]["language"] == "en":
            caption_id = item["id"]
            break

    if not caption_id:
        raise Exception("No English transcript available for this video")

    # Download and parse transcript
    caption_response = youtube_client.captions().download(
        id=caption_id
    ).execute()
    caption_text = caption_response.decode("utf-8")
    
    return parse_transcript_text(caption_text)

def convert_time_to_ms(time_str: str) -> int:
    """Convert timestamp string to milliseconds.

    Args:
        time_str: Timestamp in format 'HH:MM:SS.mmm'

    Returns:
        Time in milliseconds
    """
    hours, minutes, seconds, milliseconds = time_str.replace(".", ":").split(":")
    total_ms = (
        int(hours) * 3600000 +
        int(minutes) * 60000 +
        int(seconds) * 1000 +
        int(milliseconds)
    )
    return total_ms

def parse_transcript_text(caption_data: str) -> List[str]:
    """Parse YouTube caption data into transcript segments.

    Args:
        caption_data: Raw caption data from YouTube API

    Returns:
        List of transcript segments with timestamps at regular intervals
    """
    transcript_segments = []
    MIN_GAP_MS = 30 * 1000  # 30 seconds in milliseconds
    last_timestamp_ms = -2 * MIN_GAP_MS
    
    # Process caption blocks
    for block in caption_data.strip().split("\n\n"):
        lines = block.split("\n")
        if len(lines) >= 2:
            text = lines[1]
            if text == "e":  # Skip empty segments
                continue
            
            # Parse timing information
            timing = lines[0]
            start_time, end_time = timing.split(",")
            current_time_ms = convert_time_to_ms(start_time)
            
            # Add timestamp if enough time has passed
            if current_time_ms - last_timestamp_ms > MIN_GAP_MS:
                transcript_segments.append(f"<Timestamp: {start_time}>")
                last_timestamp_ms = current_time_ms
                
            transcript_segments.append(text)

    # Add final timestamp
    transcript_segments.append(f"<Timestamp: {end_time}>")
    return transcript_segments