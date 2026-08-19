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
# 1. HELPER FUNCTIONS & CHART
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

def generate_neurotwin_chart(threat_score, deprivation_score):
    """
    Generates a matplotlib radar chart dynamically mapping DMAP 
    Threat and Deprivation scores to specific brain circuits.
    """
    categories = [
        'Threat Reactivity\n(Amygdala / PAG)',
        'Social Cognition\n(TPJ / mPFC)',
        'Reward Sensitivity\n(Ventral Striatum)',
        'Cognitive Flexibility\n(dlPFC)',
        'Interoception\n(Insula)'
    ]
    N = len(categories)
    
    # Baseline control is set to 3.0 out of 5.0
    control_scores = [3.0, 3.0, 3.0, 3.0, 3.0] 
    
    # Map the DMAP scores to the theoretical circuits
    patient_scores = [
        threat_score,           # Threat impacts Amygdala
        3.0,                    # Social Cognition (Baseline/Variable)
        deprivation_score,      # Deprivation impacts Ventral Striatum
        deprivation_score,      # Deprivation impacts dlPFC
        threat_score            # Threat impacts Insula
    ]
    
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
# 2. DICTIONARY (Shortened for brevity)
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
        "safe_yes_reply": "Thank you. Let's begin the DMAP Inventory.",
        "safe_no_reply": "Your well-being is our priority. We have securely closed your session.",
        "decompression_prompt": "Thank you for completing this inventory. Generating your theoretical NeuroTwin topology...",
        "tab_text": "⌨️ Type Response",
        "tab_audio": "🎙️ Record Audio",
        "btn_submit_text": "Submit Assessment",
        "btn_skip": "⏭️ Skip Narrative",
        "error_empty_text": "Please type a response or choose 'Skip'.",
        "audio_inst_1": "Take all the time you need. The recording will **not** stop if you pause to think.",
        "audio_inst_2": "**1. Click the microphone ONCE to start recording.**",
        "audio_inst_3": "**2. Click it a SECOND time to stop and submit.**",
        "audio_inst_4": "⚠️ **Important:** Wait a few seconds for processing after clicking stop.",
        "processing_audio": "⏳ Processing... please wait.",
        "success": "✅ Your responses have been submitted. You may now close this window."
    }
}

# ==========================================
# 3. INITIALIZE SESSION STATES
# ==========================================
if 'responses' not in st.session_state:
    st.session_state.responses = {'id': datetime.now().strftime("%Y%m%d_%H%M%S")}
if 'admin_unlocked' not in st.session_state:
    st.session_state.admin_unlocked = False
if 'current_step' not in st.session_state:
    st.session_state.current_step = 'dashboard'
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
            if admin_password == st.secrets.get("admin_password", "1234"): 
                st.session_state.admin_unlocked = True
            else:
                st.error("Incorrect Password")

if st.session_state.admin_unlocked:
    st.title("Admin Dashboard")
    st.write("Welcome to the secure administrative view.")
    st.stop() 

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
# 6. THE STATE MACHINE 
# ==========================================
t = CONTENT[st.session_state.lang]

if st.session_state.current_step == 'dashboard':
    st.title("NeuroTwin: Many Ways to Thrive")
    st.write("### Your story. Your choices. Many ways to thrive.")
    st.write("---")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Begin Journey 🧭", use_container_width=True):
            st.session_state.current_step = 'language_selection'
            st.rerun()
    with col2:
        if st.button("Learn & Explore 📖", use_container_width=True):
            st.info("The NeuroTwin instrument uses the DMAP framework to map theoretical brain circuit topologies.")
    with col3:
        if st.button("Consent & Privacy 🔒", use_container_width=True):
            st.info("Your data is strictly confidential and anonymized.")

elif st.session_state.current_step == 'language_selection':
    st.write("### Please select your preferred language:")
    if st.button("English", use_container_width=True):
        st.session_state.lang = "English"
        st.session_state.responses['language'] = "English"
        st.session_state.messages.append({"role": "assistant", "type": "text", "content": CONTENT["English"]["welcome"]})
        st.session_state.current_step = 'intro_meal'
        st.rerun()

elif st.session_state.current_step == 'intro_meal':
    col1, col2 = st.columns(2)
    if col1.button(t["btn_meal_yes"], use_container_width=True):
        advance_chat(t["btn_meal_yes"], "text", "has_eaten", "safety_gate", t["meal_yes_reply"])
    if col2.button(t["btn_meal_no"], use_container_width=True):
        advance_chat(t["btn_meal_no"], "text", "has_eaten", "safety_gate", t["meal_no_reply"])

elif st.session_state.current_step == 'safety_gate':
    col1, col2 = st.columns(2)
    if col1.button(t["btn_safe_yes"], use_container_width=True):
        advance_chat(t["btn_safe_yes"], "text", "safe_space", "dmap_inventory", t["safe_yes_reply"])
    if col2.button(t["btn_safe_no"], use_container_width=True):
        advance_chat(t["btn_safe_no"], "text", "safe_space", "safe_exit", t["safe_no_reply"])

elif st.session_state.current_step == 'safe_exit':
    st.info("To restart the assessment, please use the sidebar button.")

# THE NEW DMAP INVENTORY MODULE
elif st.session_state.current_step == 'dmap_inventory':
    st.write("---")
    st.header("The DMAP Narrative Inventory")
    st.markdown("**Scale:** `1=Never true` | `2=Rarely true` | `3=Sometimes true` | `4=Often true` | `5=Very often true`")
    
    # DIMENSION 1: THREAT
    st.subheader("Part 1: Indicators of Threat")
    st.info("This section targets experiences that theoretically upregulate fear-learning circuits and threat vigilance.")
    options = [1, 2, 3, 4, 5]
    
    t1 = st.radio("T1: I felt a constant need to be on guard or 'walk on eggshells' in my own home.", options, index=0, horizontal=True)
    t2 = st.radio("T2: Adults in my life used intense anger, fear, or intimidation to control my behavior.", options, index=0, horizontal=True)
    t3 = st.radio("T3: I witnessed aggressive physical or verbal conflicts between people in my household.", options, index=0, horizontal=True)
    t4 = st.radio("T4: My environment felt unpredictable; I never knew what mood my caretakers would be in.", options, index=0, horizontal=True)
    t5 = st.radio("T5: I was subjected to physical discipline that felt excessive, unsafe, or unpredictable.", options, index=0, horizontal=True)
    t6 = st.radio("T6: People I depended on made me feel physically or emotionally unsafe.", options, index=0, horizontal=True)
    t7_raw = st.radio("T7 (Reverse Scored): When I made a mistake, I trusted that I would be corrected gently rather than harshly.", options, index=4, horizontal=True)
    t7_reversed = 6 - t7_raw # Reverse scoring logic applied

    st.divider()

    # DIMENSION 2: DEPRIVATION
    st.subheader("Part 2: Indicators of Deprivation")
    st.info("This section targets the absence of expected cognitive, social, or material inputs.")
    
    d1 = st.radio("D1: I went long periods without adults asking about my thoughts, feelings, or interests.", options, index=0, horizontal=True)
    d2 = st.radio("D2: My home lacked engaging things to do, such as books to read, toys, or access to hobbies.", options, index=0, horizontal=True)
    d3 = st.radio("D3: I often had to worry about whether our basic needs (like enough food, electricity, or stable housing) would be met.", options, index=0, horizontal=True)
    d4 = st.radio("D4: I was frequently left alone or unsupervised for longer than was appropriate for my age.", options, index=0, horizontal=True)
    d5 = st.radio("D5: It was rare for adults in my life to offer praise, encouragement, or affection.", options, index=0, horizontal=True)
    d6 = st.radio("D6: I did not have an adult who reliably helped me with schoolwork or taught me new skills.", options, index=0, horizontal=True)
    d7_raw = st.radio("D7 (Reverse Scored): My home environment felt mentally stimulating and full of opportunities to learn.", options, index=4, horizontal=True)
    d7_reversed = 6 - d7_raw # Reverse scoring logic applied

    # NARRATIVE CONTEXT & SUBMISSION
    st.divider()
    st.subheader("Part 3: Narrative Context (Optional)")
    st.markdown("**How did these experiences shape how you view the world today? Please feel free to share a specific memory or reflection.**")

    tab_text, tab_audio = st.tabs([t["tab_text"], t["tab_audio"]])
    
    # Calculate Averages (Score ranges from 1 to 5)
    threat_avg = (t1 + t2 + t3 + t4 + t5 + t6 + t7_reversed) / 7.0
    dep_avg = (d1 + d2 + d3 + d4 + d5 + d6 + d7_reversed) / 7.0
    
    ai_reply = t["decompression_prompt"]
    next_step = "decompression"

    with tab_text:
        user_text = st.text_area("Type your narrative here:", key="dmap_narrative_text")
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button(t["btn_submit_text"], type="primary", use_container_width=True):
                st.session_state.responses["threat_score_avg"] = threat_avg
                st.session_state.responses["deprivation_score_avg"] = dep_avg
                advance_chat(user_text if user_text.strip() else "[No Narrative Provided]", "text", "dmap_narrative", next_step, ai_reply)
                
    with tab_audio:
        st.info(t["audio_inst_1"])
        st.markdown(t["audio_inst_2"])
        st.markdown(t["audio_inst_3"])
        st.warning(t["audio_inst_4"])
        
        audio_bytes = audio_recorder(key="dmap_narrative_mic", pause_threshold=300.0)
        
        if audio_bytes:
            with st.spinner(t["processing_audio"]):
                st.session_state.responses["threat_score_avg"] = threat_avg
                st.session_state.responses["deprivation_score_avg"] = dep_avg
                audio_path = save_audio_file(audio_bytes, "dmap_narrative_audio")
                advance_chat(audio_path, "audio", "dmap_narrative", next_step, ai_reply)

# FINAL DECOMPRESSION & RADAR CHART
elif st.session_state.current_step == 'decompression':
    with st.spinner("Encrypting and syncing your data..."):
        success = export_data_to_google()
        save_data_to_json() 
        
    if success:
        st.success(t["success"])
        
        st.divider()
        st.subheader("Your NeuroTwin Topology")
        
        # Pull the dynamically calculated scores from the session state
        t_score = st.session_state.responses.get("threat_score_avg", 3.0)
        d_score = st.session_state.responses.get("deprivation_score_avg", 3.0)
        
        # Display the math
        st.write(f"**Calculated Threat Index:** {t_score:.2f} / 5.0")
        st.write(f"**Calculated Deprivation Index:** {d_score:.2f} / 5.0")
        st.write("Based on your answers, here is a theoretical mapping of your circuit topology against a neurotypical baseline.")
        
        # Render the dynamic chart!
        fig = generate_neurotwin_chart(t_score, d_score)
        st.pyplot(fig)
        
    else:
        st.error("⚠️ There was a network issue. A local backup has been safely stored.")
