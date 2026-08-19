import streamlit as st
import pandas as pd
import numpy as np

# Configure the app's appearance
st.set_page_config(page_title="NeuroContext Narrative", layout="centered")

# Initialize session state to manage the user's journey through the app
if 'stage' not in st.session_state:
    st.session_state.stage = 'safety_gate'

def next_stage(stage_name):
    st.session_state.stage = stage_name

# -----------------------------------------
# PHASE 1: The Safety Gate
# -----------------------------------------
if st.session_state.stage == 'safety_gate':
    st.title("Welcome to the NeuroContext Study")
    st.write("You are about to be asked a few questions regarding your past experiences and childhood.")
    st.warning("Are you currently in a safe, private, and comfortable environment to reflect on these topics?")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes, I am in a safe space"):
            next_stage('modality_selection')
    with col2:
        if st.button("No, I need to exit"):
            next_stage('safe_exit')

# -----------------------------------------
# PHASE 1B: Safe Exit (Triggered if "No")
# -----------------------------------------
elif st.session_state.stage == 'safe_exit':
    st.title("Your well-being is our priority.")
    st.write("It is completely okay to step away. We have securely closed your session.")
    st.info("When you feel ready and are in a private space, you can return to this link at any time.")
    if st.button("Restart Assessment"):
        next_stage('safety_gate')

# -----------------------------------------
# PHASE 2: Modality Selection
# -----------------------------------------
elif st.session_state.stage == 'modality_selection':
    st.title("How would you prefer to share your story today?")
    st.write("You can choose to either type your responses or speak them out loud.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⌨️ I prefer to type"):
            st.session_state.modality = 'text'
            next_stage('assessment')
    with col2:
        if st.button("🎙️ I prefer to speak"):
            st.session_state.modality = 'audio'
            next_stage('assessment')

# -----------------------------------------
# PHASE 3: The Narrative Prompts
# -----------------------------------------
elif st.session_state.stage == 'assessment':
    st.title("Subjective Appraisal")
    
    with st.form("assessment_form"):
        st.write("### 1. How would you describe your childhood in one word?")
        q1 = st.text_input("Your answer:") if st.session_state.modality == 'text' else st.text_input("Type or dictate your answer (Audio processing integration goes here):")
        
        st.write("### 2. How would you describe your childhood in one sentence?")
        q2 = st.text_area("Your answer:")
        
        st.write("### 3. What would you change about the way you grew up?")
        q3 = st.text_area("Your answer:")
        
        submitted = st.form_submit_button("Submit Responses")
        if submitted:
            # Here you would typically save the data to a database or Pandas DataFrame
            st.session_state.responses = {'Q1': q1, 'Q2': q2, 'Q3': q3}
            next_stage('decompression')

# -----------------------------------------
# PHASE 4: Decompression & Closing
# -----------------------------------------
elif st.session_state.stage == 'decompression':
    st.title("Thank you for sharing your experience.")
    st.success("Your perspective is vital to our research.")
    st.write("Recalling past experiences can sometimes be taxing. Please take a moment for yourself. Take a deep breath in... and out.")
    
    st.markdown("---")
    st.write("**Collected Data (For Researcher View Only):**")
    st.json(st.session_state.responses)
