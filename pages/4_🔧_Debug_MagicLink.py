import streamlit as st
from streamlit_app import work_with_ml

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
