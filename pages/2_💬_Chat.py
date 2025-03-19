import streamlit as st
from core_chat import chat_with_transcript_history

st.title("Chat Interface")

if 'videos' not in st.session_state or not st.session_state['videos']:
    st.warning("No videos processed yet. Please analyze a video first.")
else:
    # Combine all transcripts
    transcript_combined = ""
    for video_id in st.session_state['videos']:
        transcript_combined += st.session_state[str(video_id)]
    
    chat_with_transcript_history(transcript_combined, "")
