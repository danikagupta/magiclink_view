import streamlit as st

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from typing import List, Dict, Union
import googleapiclient.discovery

from pathlib import Path

def get_google_creds(credential_file_path: str) -> Credentials:
    creds = None
    #
    # Kludge!!
    #
    filepath=Path(credential_file_path)
    if filepath.exists():
        print(f"File path {credential_file_path} exists")
    else:
        print(f"Creating file: {credential_file_path}")
        refresh_token=st.secrets['refresh_token']
        token_uri=st.secrets['token_uri']
        client_id=st.secrets['client_id']
        client_secret=st.secrets['client_secret']
        scopes=st.secrets['scopes']
        content="{"+f"""

    "refresh_token": "{refresh_token}",
    "token_uri": "{token_uri}",
    "client_id": "{client_id}",
    "client_secret": "{client_secret}",
    "scopes": {scopes}
  
        """+"}"
        filepath.write_text(content)

    creds = Credentials.from_authorized_user_file(credential_file_path)
    if not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

    return creds


def get_transcript(video_id: str) -> List[Dict[str, Union[str, int]]]:
    api_service_name = "youtube"
    api_version = "v3"
    auth_location = "my2credentials.json"

    credentials = get_google_creds(auth_location)

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials
    )

    response = youtube.captions().list(part="id,snippet", videoId=video_id).execute()

    caption_id = None
    for item in response.get("items", []):
        if item["snippet"]["language"] == "en":
            caption_id = item["id"]
            break

    if not caption_id:
        raise Exception("Transcript is not available")

    caption_response = youtube.captions().download(id=caption_id).execute()
    caption_data = caption_response.decode("utf-8")
    list_transcript = parse_transcript_text(caption_data)
    
    return list_transcript

def convert_time_to_ms(time_str: str) -> int:
    h, m, s, ms = time_str.replace(".", ":").split(":")
    ms_time = (int(h) * 3600 + int(m) * 60 + int(s)) * 1000 + int(ms)
    return ms_time

def parse_transcript_text(caption_data: str) -> List[Dict[str, Union[str, int]]]:
    list_transcript = []
    MIN_GAP=30*1000
    last_published= 0 - MIN_GAP*2;
    
    for block in caption_data.strip().split("\n\n"):
        lines = block.split("\n")
        if len(lines) >= 2:
            # Extract text
            text = lines[1]
            if text == "e":
                continue
            
            # Extract timing
            timing = lines[0]
            start_time, end_time = timing.split(",")
            start_time_ms = convert_time_to_ms(start_time)
            if start_time_ms-last_published>MIN_GAP:
                list_transcript.append(f"<Timestamp: {start_time}>")
                last_published=start_time_ms
            list_transcript.append(text)

    list_transcript.append(f"<Timestamp: {end_time}>")
    return list_transcript