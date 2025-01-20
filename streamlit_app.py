import streamlit as st
import requests
import json
import os
from magiclink_chat import chat_with_transcript_history, SRC_URL, extract_magic_link, get_video_id_from_url, get_transcript

os.environ["LANGCHAIN_TRACING_V2"]="true"
os.environ["LANGCHAIN_API_KEY"]=st.secrets['LANGCHAIN_API_KEY']
os.environ["LANGCHAIN_PROJECT"]="SessionAthena"
os.environ['LANGCHAIN_ENDPOINT']="https://api.smith.langchain.com"

def extract_yt_link(m):
    return m

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

page1nav=st.Page("magiclink_chat.py",title="Magic Link Y")
page2nav=st.Page(page2,title="YT video upload X") 
page3nav=st.Page(page3, title="Chat X")
page4nav=st.Page(page4,title="Debug: YT X")
page5nav=st.Page(page5,title="Debug: MagicLink X")

pg=st.navigation([page1nav,page2nav,page3nav,page4nav,page5nav])
pg.run()
