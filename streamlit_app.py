import streamlit as st
import json
import os
from datetime import datetime
from audio_recorder_streamlit import audio_recorder

# Configure the app's appearance
st.set_page_config(page_title="DMAP Narrative Instrument", layout="centered")

# Initialize session states
if 'stage' not in st.session_state:
    st.session_state.stage = 'safety_gate'
if 'responses' not in st.session_state:
    st.session_state.responses = {'id': datetime.now().strftime("%Y%m%d_%H%M%S")}
if 'modality' not in st.session_state:
    st.session_state.modality = 'text'

# Function to instantly transition between pages
def set_stage(new_stage):
    st.session_state.stage = new_stage
    st.rerun()

# Function to save text responses to a local JSON file
def save_data_to_json():
    file_path = 'clinical_responses.json'
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            db = json.load(f)
    else:
        db = []
    
    # Check if this session's data is already saved to prevent duplicates
    if not any(entry.get('id') == st.session_state.responses['id'] for entry in db):
        db.append(st.session_state.responses)
        with open(file_path, 'w') as f:
            json.dump(db, f, indent=4)

# Function to save audio bytes to a local wav file
def save_audio_file(audio_bytes, question_key):
    filename = f"audio_{st.session_state.responses['id']}_{question_key}.wav"
    with open(filename, "wb") as f:
        f.write(audio_bytes)
    st.session_state.responses[question_key] = filename # Save the file path to the JSON log

# -----------------------------------------
# STAGE 1: The Safety Gate
# -----------------------------------------
if st.session_state.stage == 'safety_gate':
    st.title("Welcome to the Narrative Context Study")
    st.write("This instrument explores how early life experiences shape our perspectives.")
    st.warning("You are about to be asked questions regarding childhood adversity, threat, and deprivation. Are you currently in a safe, private, and comfortable environment to reflect on these topics?")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes, I am in a safe space", use_container_width=True):
            set_stage('modality_selection')
    with col2:
        if st.button("No, I need to exit", use_container_width=True):
            set_stage('safe_exit')

# -----------------------------------------
# STAGE 1B: Safe Exit 
# -----------------------------------------
elif st.session_state.stage == 'safe_exit':
    st.title("Your well-being is our priority.")
    st.write("It is completely okay to step away. We have securely closed your session.")
    if st.button("Restart Assessment"):
        set_stage('safety_gate')

# -----------------------------------------
# STAGE 2: Modality Selection
# -----------------------------------------
elif st.session_state.stage == 'modality_selection':
    st.title("Select Your Input Method")
    st.write("How would you prefer to share your narrative today?")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⌨️ I prefer to type", use_container_width=True):
            st.session_state.modality = 'text'
            set_stage('dmap_threat')
    with col2:
        if st.button("🎙️ I prefer to speak", use_container_width=True):
            st.session_state.modality = 'audio'
            set_stage('dmap_threat')
            
    st.divider()
    if st.button("⬅️ Back"):
        set_stage('safety_gate')

# -----------------------------------------
# STAGE 3: DMAP - Threat Assessment
# -----------------------------------------
elif st.session_state.stage == 'dmap_threat':
    st.title("Part 1: Experiences of Threat")
    
    st.write("### 1. Objective Recall")
    st.write("Did you experience instances where you felt physically or emotionally threatened during your childhood? Briefly describe the nature of these events.")
    
    if st.session_state.modality == 'text':
        threat_obj = st.text_area("Your response:", value=st.session_state.responses.get('threat_obj_text', ''), key='t_obj_text')
        st.session_state.responses['threat_obj_text'] = threat_obj
    else:
        st.write("🎙️ **Click the microphone to record your response:**")
        audio_bytes_1 = audio_recorder(key="threat_obj_mic")
        if audio_bytes_1:
            st.audio(audio_bytes_1, format="audio/wav")
            save_audio_file(audio_bytes_1, "threat_obj_audio")
    
    st.write("### 2. Subjective Appraisal")
    st.write("How did those specific experiences shape your understanding of safety, and how do they influence your ability to trust others today?")
    
    if st.session_state.modality == 'text':
        threat_subj = st.text_area("Your response:", value=st.session_state.responses.get('threat_subj_text', ''), key='t_subj_text')
        st.session_state.responses['threat_subj_text'] = threat_subj
    else:
        st.write("🎙️ **Click the microphone to record your response:**")
        audio_bytes_2 = audio_recorder(key="threat_subj_mic")
        if audio_bytes_2:
            st.audio(audio_bytes_2, format="audio/wav")
            save_audio_file(audio_bytes_2, "threat_subj_audio")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", use_container_width=True):
            set_stage('modality_selection')
    with col2:
        if st.button("Next ➡️", use_container_width=True):
            set_stage('dmap_deprivation')

# -----------------------------------------
# STAGE 4: DMAP - Deprivation Assessment
# -----------------------------------------
elif st.session_state.stage == 'dmap_deprivation':
    st.title("Part 2: Experiences of Deprivation")
    
    st.write("### 3. Objective Recall")
    st.write("Were there times in your childhood when you felt your basic physical or emotional needs were consistently not met?")
    
    if st.session_state.modality == 'text':
        dep_obj = st.text_area("Your response:", value=st.session_state.responses.get('dep_obj_text', ''), key='d_obj_text')
        st.session_state.responses['dep_obj_text'] = dep_obj
    else:
        st.write("🎙️ **Click the microphone to record your response:**")
        audio_bytes_3 = audio_recorder(key="dep_obj_mic")
        if audio_bytes_3:
            st.audio(audio_bytes_3, format="audio/wav")
            save_audio_file(audio_bytes_3, "dep_obj_audio")
    
    st.write("### 4. Subjective Appraisal")
    st.write("How has this absence of support or resources influenced how you view your own self-worth and how you connect with communities now?")
    
    if st.session_state.modality == 'text':
        dep_subj = st.text_area("Your response:", value=st.session_state.responses.get('dep_subj_text', ''), key='d_subj_text')
        st.session_state.responses['dep_subj_text'] = dep_subj
    else:
        st.write("🎙️ **Click the microphone to record your response:**")
        audio_bytes_4 = audio_recorder(key="dep_subj_mic")
        if audio_bytes_4:
            st.audio(audio_bytes_4, format="audio/wav")
            save_audio_file(audio_bytes_4, "dep_subj_audio")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", use_container_width=True):
            set_stage('dmap_threat')
    with col2:
        if st.button("Submit Assessment ✅", use_container_width=True):
            save_data_to_json() # Saves the text responses and file paths to JSON
            set_stage('decompression')

# -----------------------------------------
# STAGE 5: Decompression & Export
# -----------------------------------------
elif st.session_state.stage == 'decompression':
    st.title("Thank you for sharing your narrative.")
    st.success("Your perspective is vital to building a more context-aware framework for clinical care.")
    st.markdown("---")
    st.subheader("Data Successfully Saved")
    st.write("Your text responses and audio file paths have been saved to `clinical_responses.json`. Any audio recordings have been saved as `.wav` files in your project folder.")
    st.json(st.session_state.responses)
    
    import json
    import os
    
    # Create a download button for the JSON file
    if os.path.exists('clinical_responses.json'):
        with open('clinical_responses.json', 'r') as f:
            json_data = f.read()
            
        st.download_button(
            label="📥 Download JSON Data", 
            data=json_data, 
            file_name="clinical_responses.json", 
            mime="application/json" 
        )
    else:
        st.warning("No JSON data found yet.")
