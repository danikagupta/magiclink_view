"""Multi-page Streamlit application for session analysis and YouTube integration.

This module provides a multi-page interface for:
- Magic Link session analysis
- YouTube video upload and transcript analysis
- Chat interface for transcript analysis
- Debug views for both YouTube and Magic Link functionality
"""

import streamlit as st
import requests
import json
import os
from typing import List, Dict, Union, Optional

from magiclink_chat import process_magic_link, extract_video_id
from google_integration import get_transcript

# Configure LangChain environment
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = st.secrets['LANGCHAIN_API_KEY']
os.environ["LANGCHAIN_PROJECT"] = "SessionAthena"
os.environ['LANGCHAIN_ENDPOINT'] = "https://api.smith.langchain.com"

# API endpoint for fetching student session information
API_BASE_URL = "https://apigateway.navigator.pyxeda.ai/aiclub/one-on-one-student-info"

def ensure_list_of_strings(field_value: Union[str, List, None]) -> List[str]:
    """Convert various input types to a list of strings.
    
    Args:
        field_value: Input value that could be string, list, or None
        
    Returns:
        List of strings
    """
    if isinstance(field_value, list):
        return [str(item) for item in field_value]
    elif isinstance(field_value, str):
        return [field_value]
    else:
        return []

def extract_yt_videos(response: requests.Response) -> List[Dict[str, str]]:
    """Extract YouTube video information from API response.
    
    Args:
        response: API response containing session data
        
    Returns:
        List of dictionaries containing session information
    """
    rsp = json.loads(response.text)
    sessions = rsp['data']['sessions']
    final_list = []
    
    for session in sessions:
        yt_links = ensure_list_of_strings(session.get("youtube_link", ""))
        if not yt_links:
            continue
            
        session_info = {
            'date': session['session_date'],
            'youtube_url': yt_links[0],
            'youtube_count': len(yt_links),
            'instructors': ", ".join(session['instructor_names']),
            'summary': str(ensure_list_of_strings(session.get("session_summary", ""))),
            'session_id': session['session_id']
        }
        final_list.append(session_info)
        
    return final_list

def work_with_ml(link_id: str) -> None:
    """Process magic link and display session information.
    
    Args:
        link_id: Magic link identifier
    """
    st.session_state['magiclink'] = link_id
    api_url = f"{API_BASE_URL}?linkId={link_id}"
    
    response = requests.get(api_url)
    if response.status_code != 200:
        st.error(f"Error fetching data: {response.status_code}")
        return
        
    # Extract session data
    sessions = extract_yt_videos(response)
    
    # Display session data in sidebar
    with st.sidebar.expander("Session History"):
        st.dataframe(sessions)
    
    # Process only the latest session's video
    if not sessions:
        st.error("No sessions found with video content")
        return
        
    # Get the latest session (first in the list since they're ordered by date)
    latest_session = sessions[0]
    video_url = latest_session['youtube_url']
    video_id = extract_video_id(video_url)
    transcript = get_transcript(video_id)
    
    # Store in session state
    if 'videos' not in st.session_state:
        st.session_state['videos'] = []
    if video_id not in st.session_state['videos']:
        st.session_state['videos'].append(video_id)
    
    transcript_text = "\n".join(transcript)
    st.session_state[str(video_id)] = transcript_text
    
    # Show which session we're analyzing
    st.info(f"Analyzing session from {latest_session['date']}")
    
    # Prepare concise session history
    session_history = [
        {
            "date": session['date'],
            "summary": session.get('summary', '')
        }
        for session in sessions
    ]
    
    # Initialize chat interface
    from core_chat import chat_with_transcript_history
    chat_with_transcript_history(transcript_text, str(latest_session))

def work_with_yt(youtube_url: str) -> None:
    """Process YouTube URL and display transcript.
    
    Args:
        youtube_url: URL of the YouTube video
    """
    st.session_state['yt_url'] = youtube_url
    st.write(f"Processing YouTube URL: {youtube_url}")
    
    video_id = extract_video_id(youtube_url)
    st.write(f"Video ID: {video_id}")
    
    transcript = get_transcript(video_id)
    
    # Store in session state
    if 'videos' not in st.session_state:
        st.session_state['videos'] = []
    if video_id not in st.session_state['videos']:
        st.session_state['videos'].append(video_id)
    
    transcript_text = "\n".join(transcript)
    st.session_state[str(video_id)] = transcript_text
    
    # Display stats
    st.write(f"Retrieved {len(transcript)} segments totalling {len(transcript_text)} characters")

def magic_link_page():
    """Page for Magic Link analysis."""
    st.title("Magic Link Analysis")
    
    # Initialize from session state
    magic_link = st.session_state.get('magiclink', "")
    
    st.write("Sample magic link: 67cc29bf-798c-487b-93a0-ec96f9bd6a4c")
    magic_link = st.text_input("Magic Link", value=magic_link)
    
    if magic_link:
        work_with_ml(magic_link)

def youtube_page():
    """Page for YouTube video analysis."""
    st.title("YouTube Video Analysis")
    
    # Initialize from session state
    youtube_url = st.session_state.get('yt_url', "")
    
    st.write('Sample YT URL: https://youtu.be/MSCOhCffVtE')
    youtube_url = st.text_input("YouTube URL", value=youtube_url)
    
    if youtube_url:
        work_with_yt(youtube_url)

def chat_page():
    """Page for transcript chat interface."""
    st.title("Chat Interface")
    
    if 'videos' not in st.session_state or not st.session_state['videos']:
        st.warning("No videos processed yet. Please analyze a video first.")
        return
    
    # Combine all transcripts
    transcript_combined = ""
    for video_id in st.session_state['videos']:
        transcript_combined += st.session_state[str(video_id)]
    
    from core_chat import chat_with_transcript_history
    chat_with_transcript_history(transcript_combined, "")

def debug_yt_page():
    """Debug page for YouTube functionality."""
    st.title("Debug: YouTube")
    
    if 'videos' not in st.session_state:
        st.warning("No videos in session state")
        return
    
    # Display all transcripts
    transcripts = []
    for video_id in st.session_state['videos']:
        transcript = st.session_state[str(video_id)]
        transcripts.append({
            'ID': video_id,
            'Transcript': transcript,
            'Preview': transcript[:500]
        })
    
    st.dataframe(transcripts)

def debug_ml_page():
    """Debug page for Magic Link functionality."""
    st.title("Debug: Magic Link")
    
    # Initialize from session state
    magic_link = st.session_state.get('magiclink', "")
    
    st.write("Sample magic link: 67cc29bf-798c-487b-93a0-ec96f9bd6a4c")
    magic_link = st.text_input(
        "Magic Link",
        value=magic_link,
        help="Format: aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    )
    
    if magic_link:
        work_with_ml(magic_link)

def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="Session Analysis Tool",
        page_icon="🎓",
        layout="wide"
    )
    
    st.title("Magic Link Analysis")
    
    # Initialize from session state
    magic_link = st.session_state.get('magiclink', "")
    
    st.write("Sample magic link: 67cc29bf-798c-487b-93a0-ec96f9bd6a4c")
    magic_link = st.text_input("Magic Link", value=magic_link)
    
    if magic_link:
        work_with_ml(magic_link)

if __name__ == "__main__":
    main()
