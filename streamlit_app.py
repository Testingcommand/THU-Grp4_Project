import streamlit as st
import json
import os
import requests
import base64
import pandas as pd
from datetime import datetime
from audio_recorder_streamlit import audio_recorder

GOOGLE_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbyKRANC_nZCdQPnYQOUKfh-9-_bvweg-ZaCaabrRTi1tD7EGyyAPep3dhReVFZVhTW0/exec"

# Configure the app's appearance
st.set_page_config(page_title="DMAP Narrative Instrument", layout="centered")

# Initialize session states
if 'stage' not in st.session_state:
    st.session_state.stage = 'safety_gate'
if 'responses' not in st.session_state:
    st.session_state.responses = {'id': datetime.now().strftime("%Y%m%d_%H%M%S")}
if 'modality' not in st.session_state:
    st.session_state.modality = 'text'
if 'admin_unlocked' not in st.session_state:
    st.session_state.admin_unlocked = False

# --- Helper Functions ---
def set_stage(new_stage):
    st.session_state.stage = new_stage
    st.rerun()

def save_data_to_json():
    """Saves text responses locally for the Admin Dashboard to read."""
    file_path = 'clinical_responses.json'
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            db = json.load(f)
    else:
        db = []
    
    if not any(entry.get('id') == st.session_state.responses['id'] for entry in db):
        db.append(st.session_state.responses)
        with open(file_path, 'w') as f:
            json.dump(db, f, indent=4)

def save_audio_file(audio_bytes, question_key):
    """Saves recorded audio bytes to a .wav file."""
    filename = f"audio_{st.session_state.responses['id']}_{question_key}.wav"
    with open(filename, "wb") as f:
        f.write(audio_bytes)
    st.session_state.responses[question_key] = filename

def export_data_to_google():
    """Sends JSON text and Base64 encoded audio to the Google Apps Script Webhook."""
    payload = {
        "id": st.session_state.responses['id'],
        "text_data": st.session_state.responses,
        "audio_files": []
    }
    
    # Loop through the responses to find any saved audio filenames
    for key, value in st.session_state.responses.items():
        if isinstance(value, str) and value.endswith('.wav'):
            if os.path.exists(value):
                # Read the audio file and encode it
                with open(value, "rb") as f:
                    audio_bytes = f.read()
                    encoded_audio = base64.b64encode(audio_bytes).decode('utf-8')
                    
                    # Attach it to the payload
                    payload["audio_files"].append({
                        "filename": value,
                        "data": encoded_audio
                    })

    try:
        response = requests.post(GOOGLE_WEBAPP_URL, json=payload)
        return response.status_code == 200
    except Exception:
        return False

# -----------------------------------------
# ADMIN SIDEBAR & DASHBOARD (HIDDEN)
# -----------------------------------------
# The sidebar will ONLY render if "?admin=true" is added to the URL
if st.query_params.get("admin") == "true":
    with st.sidebar:
        st.subheader("Admin Access")
        admin_password = st.text_input("Password", type="password")
        if st.button("Login"):
            try:
                if admin_password == st.secrets["admin_password"]:
                    st.session_state.admin_unlocked = True
                    st.success("Admin Dashboard Unlocked")
                else:
                    st.error("Incorrect Password")
            except FileNotFoundError:
                st.error("Secrets configuration missing on server.")

if st.session_state.admin_unlocked:
    st.title("Admin Dashboard")
    st.write("Welcome to the secure administrative view.")
    
    file_path = 'clinical_responses.json'
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        if data:
            df = pd.DataFrame(data)
            st.subheader("Participant Submissions")
            st.dataframe(df, use_container_width=True)
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Data as CSV",
                data=csv,
                file_name="dmap_clinical_responses.csv",
                mime="text/csv"
            )
            
            # One-Click Audio Playback
            st.subheader("One-Click Audio Review")
            audio_found = False
            for entry in data:
                for key, val in entry.items():
                    if isinstance(val, str) and val.endswith('.wav') and os.path.exists(val):
                        audio_found = True
                        st.write(f"**ID:** `{entry['id']}` | **Prompt:** `{key}`")
                        st.audio(val, format="audio/wav")
                        
            if not audio_found:
                st.info("No audio files are currently stored on this server.")
                
            # Data Management Section
            st.divider()
            st.subheader("Data Management (Remove Test Runs)")
            st.warning("Deleting data here removes it from the app's local server. You must manually delete test rows from your Google Sheet and Google Drive.")
            
            col1, col2 = st.columns(2)
            with col1:
                delete_id = st.text_input("Enter Participant ID to delete:")
                if st.button("Delete Specific Record"):
                    new_data = [row for row in data if row.get('id') != delete_id]
                    if len(new_data) < len(data):
                        # Find and delete associated audio files for this ID
                        for entry in data:
                            if entry.get('id') == delete_id:
                                for key, val in entry.items():
                                    if isinstance(val, str) and val.endswith('.wav') and os.path.exists(val):
                                        os.remove(val)
                        
                        # Save the updated JSON
                        with open(file_path, 'w') as f:
                            json.dump(new_data, f, indent=4)
                        st.success(f"Record {delete_id} deleted!")
                        st.rerun()
                    else:
                        st.error("Participant ID not found.")
                        
            with col2:
                st.write("Wipe all data from the app:")
                if st.button("🗑️ Clear All Local Data", type="primary"):
                    # Delete all audio files locally
                    for entry in data:
                        for key, val in entry.items():
                            if isinstance(val, str) and val.endswith('.wav') and os.path.exists(val):
                                os.remove(val)
                    # Wipe the JSON file
                    with open(file_path, 'w') as f:
                        json.dump([], f, indent=4)
                    st.success("All local data and audio files cleared!")
                    st.rerun()

        else:
            st.info("No responses recorded yet.")
    else:
        st.info("The database file has not been created yet.")

    st.divider()
    if st.button("Logout"):
        st.session_state.admin_unlocked = False
        st.rerun()
        
    st.stop() # CRITICAL: This stops the public form from rendering if the admin is logged in.

# -----------------------------------------
# STAGE 1: The Safety Gate (Public View)
# -----------------------------------------
if st.session_state.stage == 'safety_gate':
    st.title("Welcome to the Narrative Context Study")
    st.write("This instrument explores how early life experiences shape our perspectives.")
    
    # --- NEW: Physical Well-being Check ---
    st.info("Your physical well-being is important to us. Have you had a meal or something to eat recently? (Good health and physical comfort help when reflecting on complex topics).")
    has_eaten = st.radio("Meal Check", ["Yes, I have eaten", "No, not recently"], horizontal=True, label_visibility="collapsed")
    st.session_state.responses['has_eaten'] = has_eaten
    
    if has_eaten == "No, not recently":
        st.write("*Tip: We gently encourage you to grab a snack or some water before beginning, but you may proceed whenever you feel ready.*")
    # --------------------------------------

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
            save_data_to_json() 
            set_stage('decompression')

# -----------------------------------------
# STAGE 5: Decompression & Export
# -----------------------------------------
elif st.session_state.stage == 'decompression':
    st.title("Thank you for sharing your narrative.")
    st.success("Your perspective is vital to building a more context-aware framework for clinical care.")
    st.markdown("---")
    
    with st.spinner("Securely saving your response..."):
        success = export_data_to_google()
        
    if success:
        st.write("Your responses have been successfully and securely submitted.")
    else:
        st.error("There was a network issue saving your response to the cloud. Your local backup has been saved.")
