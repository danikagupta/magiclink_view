import streamlit as st
from streamlit_app import work_with_yt

st.title("YouTube Video Upload")

# Initialize from session state
youtube_url = st.session_state.get('yt_url', "")

st.write('Sample YT URL: https://youtu.be/MSCOhCffVtE')
youtube_url = st.text_input("YouTube URL", value=youtube_url)

if youtube_url:
    work_with_yt(youtube_url)
