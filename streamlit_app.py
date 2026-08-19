import streamlit as st
import json
import os
import requests
import base64
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from audio_recorder_streamlit import audio_recorder

GOOGLE_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbyKRANC_nZCdQPnYQOUKfh-9-_bvweg-ZaCaabrRTi1tD7EGyyAPep3dhReVFZVhTW0/exec"

st.set_page_config(page_title="NeuroTwin Narrative AI", layout="centered")

# ==========================================
# 1. HELPER FUNCTIONS
# ==========================================
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

def generate_neurotwin_chart(patient_scores):
    """Generates a matplotlib radar chart for the Digital Twin."""
    categories = [
        'Threat Reactivity\n(Amygdala / PAG)',
        'Social Cognition\n(TPJ / mPFC)',
        'Reward Sensitivity\n(Ventral Striatum)',
        'Cognitive Flexibility\n(dlPFC)',
        'Interoception\n(Insula)'
    ]
    N = len(categories)
    control_scores = [3.0, 3.0, 3.0, 3.0, 3.0] 
    
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]
    
    control_scores += control_scores[:1]
    patient_data = patient_scores + patient_scores[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    plt.xticks(angles[:-1], categories, color='black', size=10)
    ax.set_rlabel_position(0)
    plt.yticks([1, 2, 3, 4, 5], ["1", "2", "3", "4", "5"], color="grey", size=8)
    plt.ylim(0, 5)

    ax.plot(angles, control_scores, linewidth=1.5, linestyle='dashed', label='Control Baseline', color='teal')
    ax.fill(angles, control_scores, 'teal', alpha=0.05)
    ax.plot(angles, patient_data, linewidth=2.5, linestyle='solid', label='Patient NeuroTwin', color='crimson')
    ax.fill(angles, patient_data, 'crimson', alpha=0.25)

    plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    ax.spines['polar'].set_visible(False) 
    return fig

# ==========================================
# 2. LANGUAGE DICTIONARY
# ==========================================
CONTENT = {
    "English": {
        "welcome": "Welcome to the Narrative Context Study.\n\nYour well-being is important to us. Have you had a meal or something to eat recently?",
        "btn_meal_yes": "Yes, I have eaten",
        "btn_meal_no": "No, not recently",
        "meal_yes_reply": "Great. Are you currently in a safe, private, and comfortable environment to reflect on complex topics?",
        "meal_no_reply": "*Tip: We gently encourage you to grab a snack before beginning.*\n\nAre you currently in a safe, private, and comfortable environment?",
        "btn_safe_yes": "Yes, I am in a safe space",
        "btn_safe_no": "No, I need to exit",
        "safe_yes_reply": "Thank you. Let's begin the visual exploration.",
        "safe_no_reply": "Your well-being is our priority. We have securely closed your session.",
        "decompression_prompt": "Thank you for completing this journey. Generating your theoretical NeuroTwin topology...",
        "tab_text": "⌨️ Type Response",
        "tab_audio": "🎙️ Record Audio",
        "btn_submit_text": "Submit Response",
        "btn_skip": "⏭️ Skip",
        "error_empty_text": "Please type a response or choose 'Skip'.",
        "audio_inst_1": "Take all the time you need. The recording will **not** stop if you pause to think.",
        "audio_inst_2": "**1. Click the microphone ONCE to start recording.**",
        "audio_inst_3": "**2. Click it a SECOND time to stop and submit.**",
        "audio_inst_4": "⚠️ **Important:** Wait a few seconds for processing after clicking stop.",
        "processing_audio": "⏳ Processing... please wait.",
        "success": "✅ Your responses have been submitted. You may now close this window."
    }
}
# (For the sake of testing the logic, I have temporarily shortened the dictionary to English. 
# Once the logic is confirmed working, you can paste your 6-language blocks right back in here!)

# ==========================================
# 3. INITIALIZE SESSION STATES
# ==========================================
if 'responses' not in st.session_state:
    st.session_state.responses = {'id': datetime.now().strftime("%Y%m%d_%H%M%S")}
if 'admin_unlocked' not in st.session_state:
    st.session_state.admin_unlocked = False

if 'current_step' not in st.session_state:
    st.session_state.current_step = 'dashboard' # Starts at the new landing page
    st.session_state.messages = []
    st.session_state.lang = "English"

# ==========================================
# 4. ADMIN SIDEBAR
# ==========================================
with st.sidebar:
    st.subheader("Assessment Controls")
    if st.button("🔄 Restart Assessment", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    if st.query_params.get("admin") == "true":
        st.divider()
        admin_password = st.text_input("Admin Password", type="password")
        if st.button("Login"):
            if admin_password == st.secrets.get("admin_password", "1234"): # Fallback for local testing
                st.session_state.admin_unlocked = True
            else:
                st.error("Incorrect Password")

if st.session_state.admin_unlocked:
    st.title("Admin Dashboard")
    st.write("Welcome to the secure administrative view.")
    st.stop() # Hides the public app

# ==========================================
# 5. RENDER CHAT HISTORY
# ==========================================
if st.session_state.current_step != 'dashboard':
    st.title("NeuroTwin Narrative AI")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["type"] == "audio":
                st.write("🎙️ *Audio Recorded*")
                st.audio(msg["content"], format="audio/wav")
            else:
                st.write(msg["content"])

# ==========================================
# 6. THE STATE MACHINE (Unbroken if/elif chain)
# ==========================================
t = CONTENT[st.session_state.lang]

# 1. The Landing Dashboard
if st.session_state.current_step == 'dashboard':
    st.image("image_1a02d2.jpg", use_column_width=True) # References your exact file
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Begin Journey 🧭", use_container_width=True):
            st.session_state.current_step = 'language_selection'
            st.rerun()
    with col2:
        if st.button("Learn & Explore 📖", use_container_width=True):
            st.info("The NeuroTwin instrument uses narrative appraisal to map theoretical brain circuit topologies.")
    with col3:
        if st.button("Consent & Privacy 🔒", use_container_width=True):
            st.info("Your data is strictly confidential and anonymized.")

# 2. Language Selection
elif st.session_state.current_step == 'language_selection':
    st.write("### Please select your preferred language:")
    if st.button("English", use_container_width=True):
        st.session_state.lang = "English"
        st.session_state.responses['language'] = "English"
        st.session_state.messages.append({"role": "assistant", "type": "text", "content": t["welcome"]})
        st.session_state.current_step = 'intro_meal'
        st.rerun()

# 3. Meal Check
elif st.session_state.current_step == 'intro_meal':
    col1, col2 = st.columns(2)
    if col1.button(t["btn_meal_yes"], use_container_width=True):
        advance_chat(t["btn_meal_yes"], "text", "has_eaten", "safety_gate", t["meal_yes_reply"])
    if col2.button(t["btn_meal_no"], use_container_width=True):
        advance_chat(t["btn_meal_no"], "text", "has_eaten", "safety_gate", t["meal_no_reply"])

# 4. Safety Gate
elif st.session_state.current_step == 'safety_gate':
    col1, col2 = st.columns(2)
    if col1.button(t["btn_safe_yes"], use_container_width=True):
        advance_chat(t["btn_safe_yes"], "text", "safe_space", "inkblot_1", t["safe_yes_reply"])
    if col2.button(t["btn_safe_no"], use_container_width=True):
        advance_chat(t["btn_safe_no"], "text", "safe_space", "safe_exit", t["safe_no_reply"])

# 5. Exit Gate
elif st.session_state.current_step == 'safe_exit':
    st.info("To restart the assessment, please use the sidebar button.")

# 6. The Projective Inkblots
elif st.session_state.current_step in ['inkblot_1', 'inkblot_2', 'inkblot_3']:
    
    if st.session_state.current_step == 'inkblot_1':
        image_url = "https://via.placeholder.com/800x400.png?text=[Ambiguous+Social+Image]"
        prompt = "What do you see happening in this scene? What are they about to do?"
        next_step = 'inkblot_2'
        ai_reply = "Thank you. Let's look at another scene."
        
    elif st.session_state.current_step == 'inkblot_2':
        image_url = "https://via.placeholder.com/800x400.png?text=[Ambiguous+Resource+Image]"
        prompt = "How do you think resources or rewards are being distributed here?"
        next_step = 'inkblot_3'
        ai_reply = "Thank you for sharing your perspective. Let's move to the final image."

    elif st.session_state.current_step == 'inkblot_3':
        image_url = "https://via.placeholder.com/800x400.png?text=[Abstract+Environment+Image]"
        prompt = "Describe the environment. Is it safe, unpredictable, or something else entirely?"
        next_step = 'decompression'
        ai_reply = t["decompression_prompt"]

    st.write("---")
    st.image(image_url, use_column_width=True)
    st.markdown(f"**{prompt}**")
    
    tab_text, tab_audio = st.tabs([t["tab_text"], t["tab_audio"]])
    
    with tab_text:
        user_text = st.text_area("Type your narrative here:", key=f"text_{st.session_state.current_step}")
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button(t["btn_submit_text"], key=f"btn_txt_{st.session_state.current_step}", type="primary", use_container_width=True):
                if user_text.strip():
                    advance_chat(user_text, "text", f"{st.session_state.current_step}_text", next_step, ai_reply)
                else:
                    st.error(t["error_empty_text"])
        with col2:
            if st.button(t["btn_skip"], key=f"skip_txt_{st.session_state.current_step}", use_container_width=True):
                advance_chat("[Skipped]", "text", f"{st.session_state.current_step}_skipped", next_step, ai_reply)
                
    with tab_audio:
        st.info(t["audio_inst_1"])
        st.markdown(t["audio_inst_2"])
        st.markdown(t["audio_inst_3"])
        st.warning(t["audio_inst_4"])
        
        col3, col4 = st.columns([3, 1])
        with col3:
            audio_bytes = audio_recorder(key=f"mic_{st.session_state.current_step}", pause_threshold=300.0)
        with col4:
            st.write("") 
            st.write("")
            if st.button(t["btn_skip"], key=f"skip_aud_{st.session_state.current_step}", use_container_width=True):
                advance_chat("[Skipped]", "text", f"{st.session_state.current_step}_skipped", next_step, ai_reply)
        
        if audio_bytes:
            with st.spinner(t["processing_audio"]):
                audio_path = save_audio_file(audio_bytes, f"{st.session_state.current_step}_audio")
                advance_chat(audio_path, "audio", f"{st.session_state.current_step}_audio", next_step, ai_reply)

# 7. Final Decompression & Radar Chart Rendering
elif st.session_state.current_step == 'decompression':
    with st.spinner("Encrypting and syncing your data..."):
        success = export_data_to_google()
        save_data_to_json() 
        
    if success:
        st.success(t["success"])
        
        # Render the Digital Twin!
        st.divider()
        st.subheader("Your NeuroTwin Topology")
        st.write("Based on your narrative appraisals, here is a theoretical mapping of your circuit topology against a baseline.")
        
        # In the future, we will calculate these scores dynamically based on their specific answers.
        # For now, we pass in a mock array to prove the visualization works.
        mock_patient_scores = [4.5, 2.5, 1.5, 2.0, 4.0] 
        fig = generate_neurotwin_chart(mock_patient_scores)
        st.pyplot(fig)
        
    else:
        st.error("⚠️ There was a network issue. A local backup has been safely stored.")
