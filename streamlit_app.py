import streamlit as st
import requests
import json

from typing import List, Dict, Union
import googleapiclient.discovery

from urllib.parse import urlparse, parse_qs

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

import tiktoken

from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage, ChatMessage

import os
from pathlib import Path

import json
from datetime import datetime

os.environ["LANGCHAIN_TRACING_V2"]="true"
os.environ["LANGCHAIN_API_KEY"]=st.secrets['LANGCHAIN_API_KEY']
os.environ["LANGCHAIN_PROJECT"]="SessionAthena"
os.environ['LANGCHAIN_ENDPOINT']="https://api.smith.langchain.com"

SRC_URL="https://apigateway.navigator.pyxeda.ai/aiclub/one-on-one-student-info?linkId="

def extract_magic_link(m):
    return m

def extract_yt_link(m):
    return m

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

def ensure_list_of_strings(field_value):
    if isinstance(field_value, list):
        return field_value 
    elif isinstance(field_value, str):
        return [field_value] 
    else:
        return [] 

def extract_yt_videos(response):
    rsp = json.loads(response.text)
    #print(f"Response = {rsp}\n**************\n")
    da=rsp['data']
    #print(f"Data = {da}\n**************\n")
    sess=da['sessions']
    #st.dataframe(sess)
    final_list=[]
    for se in sess:
        da=se['session_date']
        yt_links=ensure_list_of_strings(se.get("youtube_link", ""))
        yt_link_count=len(yt_links)
        yt_link1=yt_links[0]
        instructors=", ".join(se['instructor_names'])
        summary=str(ensure_list_of_strings(se.get("session_summary", "")))
        #summary='Removed'
        se_id=se['session_id']
        final_list.append({'da':da,'yt':yt_link1,'ytc':yt_link_count,'ins':instructors,'sum':summary,"seid":se_id})
    #print(f"Sess = {sess}\n**************\n")
    #st.write(rsp['data']['sessions'])
    #st.write(response.text['data']['sessions'])
    return final_list

def work_with_ml(link_id):
    #link_id="67cc29bf-798c-487b-93a0-ec96f9bd6a4c"
    req_url=SRC_URL+link_id
    st.header(f"Magic link: {req_url}")
    response=requests.get(req_url)
    st.write(f"Status code: {response.status_code}")
    eyv=extract_yt_videos(response)
    #print(f"EYV: {eyv}")
    st.dataframe(eyv)

def work_with_yt(yt_url):
    link_id="67cc29bf-798c-487b-93a0-ec96f9bd6a4c"
    #yt_url="https://youtu.be/D5LODuSkdFA"
    st.write(f"YT URL: {yt_url}")
    video_id=get_video_id_from_url(yt_url)
    st.write(f"Video ID: {video_id}")
    transcript=get_transcript(video_id)
    if 'videos' not in st.session_state:
        st.session_state['videos']=[]
    if video_id not in st.session_state['videos']:
        st.session_state['videos'].append(video_id)
    st.session_state[str(video_id)]="\n".join(transcript)
    lsize=len(transcript)
    chars=len(str(transcript))
    st.write(f"Saw {lsize} segments totalling {chars} characters")
    #print(f"Transcript: {transcript}")
    #response=requests.get(req_url)
    #st.write(f"Status code: {response.status_code}")
    #eyv=extract_yt_videos(response)
    #print(f"EYV: {eyv}")
    #st.dataframe(eyv)

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
    print(f"Latest session: {latest_info['session_date']} ")
    return latest_info

def extract_ml_content_video(rsp_json):
    sessions=rsp_json['data']['sessions']
    latest_session=get_latest_video(sessions)
    first_video=latest_session['youtube_link']
    if isinstance(first_video, list):
        first_video=first_video[0]
    new_list=[]
    for sess in sessions:
        new_list.append({"date":sess['session_date'],"summary":sess['session_summary']})

    #st.write(f"Sessions: {new_list}")
    #st.write(f"First video: {first_video}")
    return new_list, first_video

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
    with st.expander("ML data"):
        st.dataframe(mlc,hide_index=False)
    with st.expander("Video transcript"):
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

def page2():
    if 'yt_url' in st.session_state:
        yt_url=st.session_state['yt_url']
    else:
        yt_url=""

    st.write('Sample YT URL: https://youtu.be/MSCOhCffVtE')
    yt=extract_yt_link(st.text_input("Youtube URL", value=yt_url))

    if yt is None or len(yt)<1:
        st.write("Enter YT URL first!!")
    else:
        work_with_yt(yt)

def create_llm_message(prompt:str, tr:str, history:str, messages:List):
  llm_msg=[]
  llm_msg.append(SystemMessage(content=prompt))
  llm_msg.append(SystemMessage(content=f"Transcript: {tr}"))
  if(len(history)>1):
      llm_msg.append(SystemMessage(content=f"History: {history}"))
  for msg in messages:
    if msg["role"]=="user":
        llm_msg.append(HumanMessage(content=msg['content']))
    if msg["role"]=="assistant":
        llm_msg.append(AIMessage(content=msg['content']))
  return llm_msg

def chat_with_transcript_history(tr,history=""):
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(tr)
    num_tokens = len(tokens)

    SYSTEM_PROMPT=f"""
    You are a helpful and thoughtful session analysis coach who double-checks their work. 
    What follows is an educational discussion between teacher and student. 
    Please answer users' questions as well as you can. 

    You can assume that we have the full list of all of student's sessions here.
    Please count carefully - double-count if needed.
    """

    avatars={"system":"💻🧠","user":"🧑‍💼","assistant":"🎓"}
    #client=OpenAI(api_key=st.secrets['OPENAI_API_KEY'])
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key = st.secrets['OPENAI_API_KEY'])
    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.write(f" Transcript Character count={len(tr)}, tokens={num_tokens}")

    for message in st.session_state.messages:
        if message["role"] != "system":
            avatar=avatars[message["role"]]
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])
            
    if prompt := st.chat_input("Ask about this session"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        llm_msg=create_llm_message(SYSTEM_PROMPT,tr,history,st.session_state.messages)
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant", avatar=avatars["assistant"]):
            response=model.invoke(llm_msg)
            full_response=response.content
            st.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})


def page3():
    st.header("Chat Here")
    if 'videos' not in st.session_state:
        st.session_state['videos']=[]
    videolist=st.session_state['videos']
    transcript_combined=""
    for video in videolist:
        transcript_combined = transcript_combined + str(st.session_state[str(video)])
    #st.sidebar.write(f" Transcript char count: {len(transcript_combined)}")
    chat_with_transcript_history(transcript_combined,"")

def page4():
    st.header("View")
    if 'videos' not in st.session_state:
        st.session_state['videos']=[]
    videolist=st.session_state['videos']
    transcripts=[]
    for video in videolist:
        transcripts.append({'ID':str(video),'Transcript':str(st.session_state[str(video)])})
        videosection=str(st.session_state[str(video)])[:500]
        print(f"Video section #1: {videosection}")
        break
    st.dataframe(transcripts)

def page5():
    if 'magiclink' in st.session_state:
        mg_init=st.session_state['magiclink']
    else:
        mg_init=""

    st.write(f"Sample magic link: 67cc29bf-798c-487b-93a0-ec96f9bd6a4c")
    mg=extract_magic_link(st.text_input("Magic Link", value=mg_init))

    #print(f"mg is {mg}")
    #print(f"Length is {len(mg)}")
    if mg is None or len(mg)<1:
        st.write("Enter magic link first!!")
    else:
        #st.header(f"Magic link: **{mg}**")
        work_with_ml(mg)

aaa="""
tab1,tab2,tab3,tab4=st.tabs(["Magic link","YT Video","Chat","View"])
with tab1:
    page1()
with tab2:
    page2()
with tab3:
    page3()
with tab4:
    page4()
"""

pg = st.navigation([st.Page(page1,title="Magic Link"), 
                    st.Page(page2,title="YT video upload"), 
                    st.Page(page3, title="Chat"), 
                    st.Page(page4,title="Debug - YT"),
                    st.Page(page5,title="Debug - MagicLink")])
pg.run()
