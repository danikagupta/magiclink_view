import streamlit as st
import requests
import json

from urllib.parse import urlparse, parse_qs
from datetime import datetime

from core_chat import chat_with_transcript_history
from google_integration import get_transcript

SRC_URL="https://apigateway.navigator.pyxeda.ai/aiclub/one-on-one-student-info?linkId="

def extract_magic_link(m):
    return m

def get_latest_video(sessions):
    latest_session = max(sessions, key=lambda s: datetime.fromisoformat(s["session_date"].replace("Z", "+00:00")))
    latest_info = {
        "session_date": latest_session["session_date"],
        "youtube_link": latest_session.get("youtube_link", []),
        "instructor_names": latest_session.get("instructor_names", []),
        "session_summary": latest_session.get("session_summary", []),
        "project_name": latest_session.get("project_name", ""),
        "time_zone": latest_session.get("time_zone", "")
    }
    print(f"Latest info: {latest_info} ")
    return latest_info

def extract_ml_content_video(rsp_json):
    sessions=rsp_json['data']['sessions']
    latest_session=get_latest_video(sessions)
    first_video=latest_session['youtube_link']
    if isinstance(first_video, list):
        first_video=first_video[0]
    new_list=[]
    for sess in sessions:
        new_list.append({"date":sess['session_date'],"summary":str(sess['session_summary'])})

    #st.write(f"Sessions: {new_list}")
    #st.write(f"First video: {first_video}")
    return new_list, first_video

def get_video_id_from_url(url):
    url_chunks = urlparse(url)
    if not url_chunks.query:
        video_id = url_chunks.path.split("/")[-1]
        return video_id

    video_id = parse_qs(url_chunks.query).get("v", [""])[0]

    if not video_id:
        video_id = url_chunks.path.split("/")[-1]
        return video_id

    return video_id

def process_ml(link_id):
    #link_id="67cc29bf-798c-487b-93a0-ec96f9bd6a4c"
    req_url=SRC_URL+link_id
    #st.header(f"Magic link: {req_url}")
    response=requests.get(req_url)
    #st.write(f"Status code: {response.status_code}")
    rsp_json=json.loads(response.text)
    mlc,fyv=extract_ml_content_video(rsp_json)
    video_id=get_video_id_from_url(fyv)
    video_transcript=get_transcript(video_id)
    with st.sidebar.expander("ML data"):
        #st.write(mlc)
        st.dataframe(mlc,hide_index=False)
    with st.sidebar.expander("Video transcript"):
        st.dataframe(video_transcript)
    chat_with_transcript_history(str(video_transcript),str(mlc))

def page1():
    if 'magiclink' in st.session_state:
        mg_init=st.session_state['magiclink']
    else:
        mg_init=""

    st.write(f"Sample magic link: 67cc29bf-798c-487b-93a0-ec96f9bd6a4c")
    mg=extract_magic_link(st.sidebar.text_input("Type in Magic Link (aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee)", value=mg_init))

    #print(f"mg is {mg}")
    #print(f"Length is {len(mg)}")
    if mg is None or len(mg)<1:
        st.write("Enter magic link first!!")
    else:
        #st.header(f"Magic link: **{mg}**")
        process_ml(mg)

page1()