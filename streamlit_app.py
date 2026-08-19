import streamlit as st
import json
import os
import requests
import base64
import pandas as pd
from datetime import datetime
from audio_recorder_streamlit import audio_recorder

GOOGLE_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbyKRANC_nZCdQPnYQOUKfh-9-_bvweg-ZaCaabrRTi1tD7EGyyAPep3dhReVFZVhTW0/exec"

st.set_page_config(page_title="DMAP Narrative AI", layout="centered")

# --- Initialize Session States ---
if 'responses' not in st.session_state:
    st.session_state.responses = {'id': datetime.now().strftime("%Y%m%d_%H%M%S")}
if 'admin_unlocked' not in st.session_state:
    st.session_state.admin_unlocked = False

# The Chatbot State Machine
if 'current_step' not in st.session_state:
    st.session_state.current_step = 'intro_meal'
    st.session_state.messages = [
        {"role": "assistant", "type": "text", "content": "Welcome to the Narrative Context Study. This instrument explores how early life experiences shape our perspectives.\n\nYour well-being is important to us. Have you had a meal or something to eat recently? (Good health and physical comfort help when reflecting on complex topics)."}
    ]

# --- Helper Functions ---
def advance_chat(user_msg, user_type, response_key, next_step, ai_msg):
    st.session_state.responses[response_key] = user_msg
    st.session_state.messages.append({"role": "user", "type": user_type, "content": user_msg})
    if ai_msg:
        st.session_state.messages.append({"role": "assistant", "type": "text", "content": ai_msg})
    st.session_state.current_step = next_step
    st.rerun()

def save_data_to_json():
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
    filename = f"audio_{st.session_state.responses['id']}_{question_key}.wav"
    with open(filename, "wb") as f:
        f.write(audio_bytes)
    return filename

def export_data_to_google():
    payload = {
        "id": st.session_state.responses['id'],
        "text_data": st.session_state.responses,
        "audio_files": []
    }
    for key, value in st.session_state.responses.items():
        if isinstance(value, str) and value.endswith('.wav') and os.path.exists(value):
            with open(value, "rb") as f:
                encoded_audio = base64.b64encode(f.read()).decode('utf-8')
                payload["audio_files"].append({"filename": value, "data": encoded_audio})
    try:
        response = requests.post(GOOGLE_WEBAPP_URL, json=payload)
        return response.status_code == 200
    except Exception:
        return False

# -----------------------------------------
# ADMIN SIDEBAR & DASHBOARD (HIDDEN)
# -----------------------------------------
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
            st.download_button(label="📥 Download Data as CSV", data=csv, file_name="dmap_clinical_responses.csv", mime="text/csv")
            
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
                
            st.divider()
            st.subheader("Data Management (Remove Test Runs)")
            col1, col2 = st.columns(2)
            with col1:
                delete_id = st.text_input("Enter Participant ID to delete:")
                if st.button("Delete Specific Record"):
                    new_data = [row for row in data if row.get('id') != delete_id]
                    if len(new_data) < len(data):
                        for entry in data:
                            if entry.get('id') == delete_id:
                                for key, val in entry.items():
                                    if isinstance(val, str) and val.endswith('.wav') and os.path.exists(val):
                                        os.remove(val)
                        with open(file_path, 'w') as f:
                            json.dump(new_data, f, indent=4)
                        st.success(f"Record {delete_id} deleted!")
                        st.rerun()
                    else:
                        st.error("Participant ID not found.")
            with col2:
                st.write("Wipe all data from the app:")
                if st.button("🗑️ Clear All Local Data", type="primary"):
                    for entry in data:
                        for key, val in entry.items():
                            if isinstance(val, str) and val.endswith('.wav') and os.path.exists(val):
                                os.remove(val)
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
    st.stop()

# -----------------------------------------
# STAGE 1: THE AI CHAT INTERFACE
# -----------------------------------------
st.title("Narrative Context AI")

# Render all previous chat bubbles
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["type"] == "audio":
            st.write("🎙️ *Audio Response Recorded*")
            st.audio(msg["content"], format="audio/wav")
        else:
            st.write(msg["content"])

# -----------------------------------------
# STAGE 2: DYNAMIC INPUT HANDLING
# -----------------------------------------
# A. Meal Check
if st.session_state.current_step == 'intro_meal':
    col1, col2 = st.columns(2)
    if col1.button("Yes, I have eaten", use_container_width=True):
        advance_chat("Yes, I have eaten.", "text", "has_eaten", "safety_gate", "Great. You are about to be asked questions regarding childhood adversity, threat, and deprivation. Are you currently in a safe, private, and comfortable environment to reflect on these topics?")
    if col2.button("No, not recently", use_container_width=True):
        advance_chat("No, not recently.", "text", "has_eaten", "safety_gate", "*Tip: We gently encourage you to grab a snack or some water before beginning.* \n\nYou are about to be asked questions regarding childhood adversity, threat, and deprivation. Are you currently in a safe, private, and comfortable environment to reflect on these topics?")

# B. Safety Gate
elif st.session_state.current_step == 'safety_gate':
    col1, col2 = st.columns(2)
    if col1.button("Yes, I am in a safe space", use_container_width=True):
        advance_chat("Yes, I am in a safe space.", "text", "safe_space", "threat_obj", "Thank you. Let's begin Part 1: Experiences of Threat.\n\nDid you experience instances where you felt physically or emotionally threatened during your childhood? Briefly describe the nature of these events.")
    if col2.button("No, I need to exit", use_container_width=True):
        advance_chat("No, I need to exit.", "text", "safe_space", "safe_exit", "Your well-being is our priority. It is completely okay to step away. We have securely closed your session.")

# C. Exit Gate
elif st.session_state.current_step == 'safe_exit':
    if st.button("Restart Assessment"):
        st.session_state.clear()
        st.rerun()

# D. The Core DMAP Questions (Tabbed Interface)
elif st.session_state.current_step in ['threat_obj', 'threat_subj', 'dep_obj', 'dep_subj']:
    
    # Determine the next step and AI reply
    if st.session_state.current_step == 'threat_obj':
        next_step = 'threat_subj'
        ai_reply = "Thank you for sharing that. How did those specific experiences shape your understanding of safety, and how do they influence your ability to trust others today?"
    elif st.session_state.current_step == 'threat_subj':
        next_step = 'dep_obj'
        ai_reply = "Part 2: Experiences of Deprivation.\n\nWere there times in your childhood when you felt your basic physical or emotional needs were consistently not met?"
    elif st.session_state.current_step == 'dep_obj':
        next_step = 'dep_subj'
        ai_reply = "How has this absence of support or resources influenced how you view your own self-worth and how you connect with communities now?"
    elif st.session_state.current_step == 'dep_subj':
        next_step = 'decompression'
        ai_reply = "Thank you for sharing your narrative. Your perspective is vital to building a more context-aware framework for clinical care. Please wait a moment while I securely save your responses..."

    st.write("---")
    
    # NEW: Tabbed interface cleanly separates typing vs. speaking
    tab_text, tab_audio = st.tabs(["⌨️ Type Response", "🎙️ Record Audio"])
    
    with tab_text:
        user_text = st.text_area("Type your response here:", key=f"text_{st.session_state.current_step}")
        if st.button("Submit Text Response", key=f"btn_txt_{st.session_state.current_step}", type="primary"):
            if user_text.strip():
                advance_chat(user_text, "text", f"{st.session_state.current_step}_text", next_step, ai_reply)
            else:
                st.error("Please type a response before submitting.")
                
    with tab_audio:
        st.info("Take all the time you need. The recording will **not** stop if you pause to think.")
        st.markdown("**1. Click the microphone icon ONCE to start recording.**")
        st.markdown("**2. Click it a SECOND time to stop recording and submit.**")
        
        audio_bytes = audio_recorder(
            key=f"mic_{st.session_state.current_step}",
            pause_threshold=300.0 
        )
        
        if audio_bytes:
            audio_path = save_audio_file(audio_bytes, f"{st.session_state.current_step}_audio")
            advance_chat(audio_path, "audio", f"{st.session_state.current_step}_audio", next_step, ai_reply)

# E. Decompression & Export
elif st.session_state.current_step == 'decompression':
    
    st.info("⏳ **Please note:** Uploading audio files to the secure server can take up to a minute depending on your connection. Please do not close or refresh this window until you see the success message below.")
    
    with st.spinner("Encrypting and syncing your data to Google Drive..."):
        success = export_data_to_google()
        save_data_to_json() 
        
    if success:
        st.success("✅ Your responses have been successfully and securely submitted. You may now safely close this window.")
    else:
        st.error("⚠️ There was a network issue saving your response to the cloud. A local backup has been safely stored.")
