# Author: Steven Lansangan
# Streamlit dashboard for testing
# Just a simple UI to verify things works
import streamlit as st
import json
import logging
from utils import memory_manager
from backend import babaru_brain

# Page Config
st.set_page_config(
    page_title="Babaru Cloud",
    page_icon="🤖",
    layout="wide"
)

# Initialize Session State
if "user_id" not in st.session_state:
    st.session_state.user_id = "user_default_01"
    # Ensure database is init
    memory_manager.init_db()
    memory_manager.create_user(st.session_state.user_id, "Creator", "UTC") 

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Sidebar: Mission Control ---
with st.sidebar:
    st.title("Babaru Control")
    
    # User Selector (Debug)
    user_id_input = st.text_input("User ID", value=st.session_state.user_id)
    if user_id_input != st.session_state.user_id:
        st.session_state.user_id = user_id_input
        st.session_state.messages = [] # Reset chat on user switch
        st.experimental_rerun()
        
    memory = memory_manager.get_user_memory(st.session_state.user_id)
    
    st.divider()
    
    if memory:
        st.subheader("Current Mission")
        active_missions = memory.get('missions', {}).get('active', [])
        if active_missions:
            for mission in active_missions:
                st.info(f"🎯 {mission}")
        else:
            st.warning("No active mission.")
            
        st.subheader("Action")
        if st.button("Submit Mission Update"):
             # In a real app, this would open a form or upload modal
             # For simulation, we pretend we are sending a "Mission Review" context
             response = babaru_brain.get_response(
                 st.session_state.user_id, 
                 "I am submitting my mission proof. [IMAGE PLACEHOLDER]", 
                 "CONTEXT_MISSION_REVIEW"
             )
             st.session_state.messages.append({"role": "user", "content": "Checking in my mission..."})
             st.session_state.messages.append({"role": "assistant", "content": response})
             st.experimental_rerun()

    st.divider()
    
    # Memory Inspector
    with st.expander("🧠 Memory Inspector (Debug)"):
        st.json(memory)

# --- Main Interface ---

# Header
if memory:
    col1, col2, col3 = st.columns(3)
    progression = memory.get('progression', {})
    with col1:
        st.metric("Rank", progression.get('rank', 'Newcomer'))
    with col2:
        st.metric("XP Points", progression.get('points', 0))
    with col3:
        st.metric("Streak", f"{progression.get('streak_days', 0)} Days")

st.divider()

# Chat Interface
st.subheader("💬 Chat with Babaru")

# Display history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input
if prompt := st.chat_input("Say something to Babaru..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Context detection (Simulated)
    # We could implement a classifier here, but for now we default to GENERAL
    # unless specific keywords are found
    trigger = "CONTEXT_GENERAL"
    if "stuck" in prompt.lower():
        trigger = "CONTEXT_USER_STUCK"
    elif "morning" in prompt.lower():
        trigger = "CONTEXT_MORNING"

    # Get AI Response
    with st.spinner("Babaru is judging you..."):
        try:
            response = babaru_brain.get_response(st.session_state.user_id, prompt, trigger)
        except Exception as e:
            response = f"Error: {str(e)}"
    
    # Add AI message
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)

