import streamlit as st
import tiktoken

from langchain_openai import ChatOpenAI

from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage, ChatMessage
from typing import List

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