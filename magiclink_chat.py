"""Magic Link Chat Interface for Educational Sessions.

This module provides a Streamlit interface for analyzing educational sessions
using magic links. It fetches session data, extracts video transcripts, and
provides an interactive chat interface for analysis.
"""

import streamlit as st
import requests
import json
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from typing import Dict, List, Tuple, Any

from core_chat import chat_with_transcript_history
from google_integration import get_transcript

# API endpoint for fetching student session information
API_BASE_URL = "https://apigateway.navigator.pyxeda.ai/aiclub/one-on-one-student-info"

def validate_magic_link(magic_link: str) -> str:
    """Validate and return the magic link.

    Args:
        magic_link: The magic link string to validate

    Returns:
        The validated magic link
    """
    return magic_link

def get_latest_session_info(sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Get information about the most recent session.

    Args:
        sessions: List of session data dictionaries

    Returns:
        Dictionary containing latest session information
    """
    # Find the most recent session by date
    latest_session = max(
        sessions,
        key=lambda s: datetime.fromisoformat(s["session_date"].replace("Z", "+00:00"))
    )
    
    # Extract relevant session information
    session_info = {
        "session_date": latest_session["session_date"],
        "youtube_link": latest_session.get("youtube_link", []),
        "instructor_names": latest_session.get("instructor_names", []),
        "session_summary": latest_session.get("session_summary", []),
        "project_name": latest_session.get("project_name", ""),
        "time_zone": latest_session.get("time_zone", "")
    }
    
    print(f"Latest session info: {session_info}")
    return session_info

def extract_session_data(response_json: Dict[str, Any]) -> Tuple[List[Dict[str, str]], str]:
    """Extract session data and video URL from API response.

    Args:
        response_json: JSON response from the API

    Returns:
        Tuple containing:
            - List of session summaries with dates
            - URL of the first video from the latest session
    """
    sessions = response_json['data']['sessions']
    latest_session = get_latest_session_info(sessions)
    
    # Get video URL from latest session
    video_url = latest_session['youtube_link']
    if isinstance(video_url, list):
        video_url = video_url[0]
    
    # Create summary list of all sessions
    session_summaries = [
        {
            "date": session['session_date'],
            "summary": str(session['session_summary'])
        }
        for session in sessions
    ]
    
    return session_summaries, video_url

def extract_video_id(url: str) -> str:
    """Extract YouTube video ID from various URL formats.

    Args:
        url: YouTube video URL

    Returns:
        YouTube video ID
    """
    parsed_url = urlparse(url)
    
    # Handle URLs without query parameters (e.g., youtu.be/VIDEO_ID)
    if not parsed_url.query:
        return parsed_url.path.split("/")[-1]
    
    # Handle standard YouTube URLs (e.g., youtube.com/watch?v=VIDEO_ID)
    video_id = parse_qs(parsed_url.query).get("v", [""])[0]
    if not video_id:
        return parsed_url.path.split("/")[-1]
    
    return video_id

def process_magic_link(link_id: str) -> None:
    """Process a magic link to display session data and chat interface.

    Args:
        link_id: The magic link identifier
    """
    # Fetch session data from API
    api_url = f"{API_BASE_URL}?linkId={link_id}"
    response = requests.get(api_url)
    session_data = json.loads(response.text)
    
    # Extract session information and video transcript
    session_summaries, video_url = extract_session_data(session_data)
    video_id = extract_video_id(video_url)
    video_transcript = get_transcript(video_id)
    
    # Display session data in sidebar
    with st.sidebar.expander("Session History"):
        st.dataframe(session_summaries, hide_index=False)
    with st.sidebar.expander("Video Transcript"):
        st.dataframe(video_transcript)
    
    # Initialize chat interface
    chat_with_transcript_history(
        str(video_transcript),
        str(session_summaries)
    )

def main() -> None:
    """Main application entry point.

    Displays the magic link input interface and processes the link
    when provided.
    """
    # Initialize magic link from session state if available
    initial_link = st.session_state.get('magiclink', "")
    
    # Display sample magic link and input field
    st.write("Sample magic link: 67cc29bf-798c-487b-93a0-ec96f9bd6a4c")
    magic_link = validate_magic_link(
        st.sidebar.text_input(
            "Type in Magic Link (aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee)",
            value=initial_link
        )
    )
    
    # Process magic link if provided
    if not magic_link:
        st.write("Please enter a magic link to begin")
    else:
        process_magic_link(magic_link)

if __name__ == "__main__":
    main()