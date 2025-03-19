import streamlit as st

st.title("Debug: YouTube")

if 'videos' not in st.session_state:
    st.warning("No videos in session state")
else:
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
