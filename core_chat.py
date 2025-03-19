"""Core chat functionality for the session analysis system.

This module provides the core chat functionality for interacting with transcripts
and session histories using LangChain and Streamlit.
"""

import streamlit as st
import tiktoken
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from typing import List, Dict

def create_llm_message(system_prompt: str, transcript: str, history: str, 
                      chat_messages: List[Dict[str, str]]) -> List[SystemMessage | HumanMessage | AIMessage]:
    """Create a list of LangChain messages for the LLM conversation.

    Args:
        system_prompt: The initial system prompt defining the assistant's role
        transcript: The session transcript text
        history: Previous session history
        chat_messages: List of previous chat messages with roles and content

    Returns:
        List of LangChain message objects for the conversation
    """
    llm_messages = [
        SystemMessage(content=system_prompt),
        SystemMessage(content=f"Transcript: {transcript}")
    ]
    
    if len(history) > 1:
        llm_messages.append(SystemMessage(content=f"History: {history}"))
    
    for msg in chat_messages:
        if msg["role"] == "user":
            llm_messages.append(HumanMessage(content=msg['content']))
        elif msg["role"] == "assistant":
            llm_messages.append(AIMessage(content=msg['content']))
            
    return llm_messages

def chat_with_transcript_history(transcript: str, history: str = "") -> None:
    """Create an interactive chat interface for analyzing session transcripts.

    Args:
        transcript: The session transcript to analyze
        history: Optional previous session history
    """
    # Calculate token count for the transcript
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(transcript)
    num_tokens = len(tokens)

    SYSTEM_PROMPT = """
    You are a helpful and thoughtful session analysis coach who double-checks their work. 
    What follows is an educational discussion between teacher and student. 
    Please answer users' questions as well as you can. 

    You can assume that we have the full list of all of student's sessions here.
    Please count carefully - double-count if needed.
    """

    # Define avatars for different roles in the chat
    AVATARS = {
        "system": "💻🧠",
        "user": "🧑‍💼",
        "assistant": "🎓"
    }

    # Initialize the chat model
    model = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=st.secrets['OPENAI_API_KEY']
    )

    # Initialize session state for messages if not exists
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display transcript statistics
    st.write(f"Transcript Character count={len(transcript)}, tokens={num_tokens}")

    # Display existing chat messages
    for message in st.session_state.messages:
        if message["role"] != "system":
            avatar = AVATARS[message["role"]]
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])

    # Handle new user input
    if user_input := st.chat_input("Ask about this session"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Create LLM messages and get response
        llm_messages = create_llm_message(
            SYSTEM_PROMPT, transcript, history, st.session_state.messages
        )
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Get and display assistant response
        with st.chat_message("assistant", avatar=AVATARS["assistant"]):
            response = model.invoke(llm_messages)
            assistant_response = response.content
            st.markdown(assistant_response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({
            "role": "assistant", 
            "content": assistant_response
        })