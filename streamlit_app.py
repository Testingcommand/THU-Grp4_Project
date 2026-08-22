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

# ==========================================
# APP CONFIGURATION
# ==========================================
GOOGLE_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzn15OGyoLn63kf3TN62iDPRVWMDGragOWEGdYiTweO3_tdUYcyFc_JzN8A5p2hFV5W/exec"

# TOGGLE THIS TO FALSE TO HIDE THE RADAR MAP AT THE END
SHOW_RADAR_MAP = False 

st.set_page_config(page_title="NeuroTwin Narrative AI", layout="centered")

st.markdown("""
    <style>
        .reportview-container { margin-top: -2em; }
        header [data-testid="stHeaderActionElements"] button { color: #808495 !important; }
        header [data-testid="stHeaderActionElements"] svg { fill: #808495 !important; stroke: #808495 !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# HELPER FUNCTIONS 
# ==========================================
def advance_chat(user_msg, user_type, response_key, next_step, ai_msg=None):
    if response_key:
        st.session_state.responses[response_key] = user_msg
    if user_msg:
        st.session_state.messages.append({"role": "user", "type": user_type, "content": user_msg})
    if ai_msg:
        st.session_state.messages.append({"role": "assistant", "type": "text", "content": ai_msg})
    st.session_state.current_step = next_step
    st.rerun()

def export_data_to_google():
    payload = {
        "id": st.session_state.responses['id'],
        "text_data": st.session_state.responses,
        "audio_files": []
    }
    # Currently only text is required in this new iteration, but audio logic remains if added back
    try:
        response = requests.post(GOOGLE_WEBAPP_URL, json=payload)
        return response.status_code == 200
    except Exception:
        return False

def generate_neurotwin_chart(threat_score, deprivation_score, war_score, col_score):
    categories = ['Threat Reactivity', 'Social Cognition', 'Reward Sensitivity', 'Cognitive Flexibility', 'Interoception']
    N = len(categories)
    control_scores = [3.0, 3.0, 3.0, 3.0, 3.0] 
    
    # Averaging War and Threat for the Threat axis, as both engage Salience
    combined_threat = (threat_score + war_score) / 2 if war_score > 0 else threat_score
    
    patient_scores = [combined_threat, col_score, deprivation_score, deprivation_score, combined_threat]
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]
    control_scores += control_scores[:1]
    patient_data = patient_scores + patient_scores[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    plt.xticks(angles[:-1], categories, color='black', size=11)
    ax.set_rlabel_position(0)
    plt.yticks([1, 2, 3, 4, 5], ["1", "2", "3", "4", "5"], color="grey", size=8)
    plt.ylim(0, 5)
    ax.plot(angles, control_scores, linewidth=1.5, linestyle='dashed', color='teal')
    ax.fill(angles, control_scores, 'teal', alpha=0.05)
    ax.plot(angles, patient_data, linewidth=2.5, linestyle='solid', color='crimson')
    ax.fill(angles, patient_data, 'crimson', alpha=0.25)
    ax.spines['polar'].set_visible(False) 
    return fig

# ==========================================
# LANGUAGE DICTIONARY
# ==========================================
# Using English base for all to prevent crashes; translation required for non-English keys later.
ENG_BASE = {
    "gate1_q": "Are you currently in a safe, private, and comfortable environment to reflect on personal topics?",
    "gate1_yes": "Yes, I am in a safe space",
    "gate1_no": "No, I need to exit",
    
    "gate2_q": "This questionnaire asks about childhood experiences, some of which may be difficult to reflect on. You can skip any question or stop at any time. Do you wish to continue?",
    "gate2_yes": "Yes, I wish to continue",
    "gate2_no": "No, I would like to stop",
    
    "mid_gate_q": "You've completed the first part. Before we continue to the next section, how are you feeling right now?",
    "mid_gate_continue": "I'm comfortable continuing",
    "mid_gate_break": "I'd like to take a break",
    "mid_gate_stop": "I'd like to stop here",
    
    "post_gate_q": "Thank you for completing this. Reflecting on past experiences can bring up emotions. How are you feeling right now?",
    "post_gate_fine": "I feel fine",
    "post_gate_unsettled": "I feel a bit unsettled but okay",
    "post_gate_talk": "I would like to talk to someone",
    
    "crisis_msg": "If you need immediate support, please contact one of the following services:",
    "crisis_resources": "- **National Crisis Line:** Dial 988\n- **Crisis Text Line:** Text HOME to 741741",
    
    "safe_exit_msg": "Your well-being is our priority. We have securely closed your session. You may close this window.",
    "break_msg": "Take all the time you need. Leave this window open, and click below when you are ready to resume.",
    "btn_resume": "I am ready to resume",
    
    "skip_note": "💙 *Gentle reminder: You may skip any question and leave it blank if you prefer not to answer.*",
    "scale_desc": "**Scale:** `1=Never true` | `2=Rarely true` | `3=Sometimes true` | `4=Often true` | `5=Very often true`",
    "btn_continue": "Continue",
    
    "part1_title": "Part 1: Indicators of Threat",
    "t1": "T1: I felt a constant need to be on guard or 'walk on eggshells' in my own home.",
    "t2": "T2: Adults in my life used intense anger, fear, or intimidation to control my behavior.",
    "t3": "T3: I witnessed aggressive physical or verbal conflicts between people in my household.",
    "t4": "T4: My environment felt unpredictable; I never knew what mood my caretakers would be in.",
    "t5": "T5: I was subjected to physical discipline that felt excessive, unsafe, or unpredictable.",
    "t6": "T6: People I depended on made me feel physically or emotionally unsafe.",
    "t7": "T7 (Reverse): When I made a mistake, I trusted that I would be corrected gently rather than harshly.",
    "t_narrative_1": "Did you experience instances where you felt physically or emotionally threatened during your childhood? Briefly describe the nature of these events.",
    "t_narrative_2": "How did those specific experiences influence your ability to trust others today?",
    
    "part2_title": "Part 2: Indicators of Deprivation",
    "d1": "D1: I went long periods without adults asking about my thoughts, feelings, or interests.",
    "d2": "D2: My home lacked engaging things to do, such as books to read, toys, or access to hobbies.",
    "d3": "D3: I often had to worry about whether our basic needs (like enough food, electricity, or stable housing) would be met.",
    "d4": "D4: I was frequently left alone or unsupervised for longer than was appropriate for my age.",
    "d5": "D5: It was rare for adults in my life to offer praise, encouragement, or affection.",
    "d6": "D6: I did not have an adult who reliably helped me with schoolwork or taught me new skills.",
    "d7": "D7 (Reverse): My home environment felt mentally stimulating and full of opportunities to learn.",
    "d_narrative_1": "Were there times in your childhood when you felt your basic physical or emotional needs were consistently not met?",
    "d_narrative_2": "How has this absence of support or resources influenced how you connect with others now?",
    
    "part3_title": "Part 3: War & Conflict Exposure",
    "w1": "W1: I grew up in an area where armed conflict, bombings, or military operations were happening around me.",
    "w2": "W2: I was forced to leave my home or community because of violence or conflict.",
    "w3": "W3: I witnessed people being seriously injured or killed as a result of conflict or organized violence.",
    "w4": "W4: I lost a family member or someone close to me to war, armed conflict, or political violence.",
    "w5": "W5: I lived in an environment where I had to constantly figure out who could be trusted and who might be dangerous.",
    "w6": "W6: My community or neighborhood was destroyed or seriously disrupted by conflict or organized violence.",
    "w7": "W7 (Reverse): Even during difficult times, my community remained stable and I felt a sense of collective safety.",
    
    "part4_title": "Part 4: Community & Cultural Context",
    "c1": "C1: When something goes wrong in my life, the first thing I do is reach out to the people around me.",
    "c2": "C2: I see myself as part of a group first, and as an individual second.",
    "c3": "C3: Decisions that affect my family or community should be made together, not by one person alone.",
    "c4": "C4: I would describe my personal identity as closely tied to the groups I belong to.",
    "c5": "C5: When I succeed, I feel it is because of the support of the people around me, not just my own effort.",
    "c6": "C6: If I had to choose between personal achievement and the well-being of my group, I would choose my group.",
    
    "part5_title": "Part 5: Narrative Context",
    "final_q1": "If you could change one thing about your childhood, what would it be?",
    "final_q2": "In one word, how did that experience shape who you are today?",
    "final_q3": "In one sentence, what do you do when you feel unsafe?"
}

CONTENT = {
    "English": ENG_BASE,
    "Mandarin": ENG_BASE,
    "Cantonese": ENG_BASE,
    "Spanish": ENG_BASE,
    "French": ENG_BASE,
    "Russian": ENG_BASE
}

# ==========================================
# INITIALIZATION
# ==========================================
if 'responses' not in st.session_state:
    st.session_state.responses = {'id': datetime.now().strftime("%Y%m%d_%H%M%S")}
if 'current_step' not in st.session_state:
    st.session_state.current_step = 'dashboard'
    st.session_state.messages = []
    st.session_state.lang = "English"

# ==========================================
# THE STATE MACHINE 
# ==========================================
t = CONTENT[st.session_state.lang]

if st.session_state.current_step == 'dashboard':
    st.title("NeuroTwin: Many Ways to Thrive")
    st.write("### Your story. Your choices. Many ways to thrive.")
    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Begin Journey 🧭", use_container_width=True):
            st.session_state.current_step = 'language_selection'
            st.rerun()
    with col2:
        if st.button("Consent & Privacy 🔒", use_container_width=True):
            st.info("Your data is strictly confidential and anonymized.")

elif st.session_state.current_step == 'language_selection':
    st.write("### Please select your preferred language:")
    cols = st.columns(3)
    langs = ["English", "Mandarin", "Cantonese", "Spanish", "French", "Russian"]
    for i, lang in enumerate(langs):
        if cols[i%3].button(lang, use_container_width=True):
            st.session_state.lang = lang
            st.session_state.responses['language'] = lang
            st.session_state.current_step = 'pre_gate_1'
            st.rerun()

# --- GATES ---
elif st.session_state.current_step == 'pre_gate_1':
    st.write("---")
    st.subheader(t["gate1_q"])
    col1, col2 = st.columns(2)
    if col1.button(t["gate1_yes"], use_container_width=True):
        st.session_state.current_step = 'pre_gate_2'
        st.rerun()
    if col2.button(t["gate1_no"], use_container_width=True):
        st.session_state.current_step = 'safe_exit'
        st.rerun()

elif st.session_state.current_step == 'pre_gate_2':
    st.write("---")
    st.warning(t["gate2_q"])
    col1, col2 = st.columns(2)
    if col1.button(t["gate2_yes"], use_container_width=True):
        st.session_state.current_step = 'dmap_part1'
        st.rerun()
    if col2.button(t["gate2_no"], use_container_width=True):
        st.session_state.current_step = 'safe_exit'
        st.rerun()

elif st.session_state.current_step == 'safe_exit':
    st.info(t["safe_exit_msg"])
    if st.button("Restart"):
        st.session_state.clear()
        st.rerun()

elif st.session_state.current_step == 'break_screen':
    st.info(t["break_msg"])
    if st.button(t["btn_resume"], type="primary"):
        st.session_state.current_step = 'dmap_part2'
        st.rerun()

# --- PART 1: THREAT ---
elif st.session_state.current_step == 'dmap_part1':
    st.write("---")
    st.header(t["part1_title"])
    st.markdown(t["skip_note"])
    st.markdown(t["scale_desc"])
    
    options = [1, 2, 3, 4, 5]
    t1 = st.radio(t["t1"], options, index=None, horizontal=True)
    t2 = st.radio(t["t2"], options, index=None, horizontal=True)
    t3 = st.radio(t["t3"], options, index=None, horizontal=True)
    t4 = st.radio(t["t4"], options, index=None, horizontal=True)
    t5 = st.radio(t["t5"], options, index=None, horizontal=True)
    t6 = st.radio(t["t6"], options, index=None, horizontal=True)
    t7_raw = st.radio(t["t7"], options, index=None, horizontal=True)
    
    st.divider()
    st.write("**Narrative Reflection (Optional)**")
    t_narrative_1 = st.text_area(t["t_narrative_1"])
    t_narrative_2 = st.text_area(t["t_narrative_2"])

    if st.button(t["btn_continue"], type="primary"):
        st.session_state.responses.update({
            "t1": t1, "t2": t2, "t3": t3, "t4": t4, "t5": t5, "t6": t6, "t7": t7_raw,
            "threat_narrative_1": t_narrative_1, "threat_narrative_2": t_narrative_2
        })
        t_scores = [t1, t2, t3, t4, t5, t6, (6 - t7_raw) if t7_raw is not None else None]
        t_answered = [s for s in t_scores if s is not None]
        st.session_state.responses["threat_score_avg"] = sum(t_answered) / len(t_answered) if len(t_answered) > 0 else 0
        
        st.session_state.current_step = 'mid_gate'
        st.rerun()

# --- MID-ASSESSMENT CHECK ---
elif st.session_state.current_step == 'mid_gate':
    st.write("---")
    st.subheader(t["mid_gate_q"])
    st.session_state.responses["mid_gate_status"] = "Completed"
    
    if st.button(t["mid_gate_continue"], use_container_width=True):
        st.session_state.current_step = 'dmap_part2'
        st.rerun()
    if st.button(t["mid_gate_break"], use_container_width=True):
        st.session_state.current_step = 'break_screen'
        st.rerun()
    if st.button(t["mid_gate_stop"], use_container_width=True):
        st.session_state.current_step = 'safe_exit'
        st.rerun()

# --- PART 2: DEPRIVATION ---
elif st.session_state.current_step == 'dmap_part2':
    st.write("---")
    st.header(t["part2_title"])
    st.markdown(t["skip_note"])
    
    options = [1, 2, 3, 4, 5]
    d1 = st.radio(t["d1"], options, index=None, horizontal=True)
    d2 = st.radio(t["d2"], options, index=None, horizontal=True)
    d3 = st.radio(t["d3"], options, index=None, horizontal=True)
    d4 = st.radio(t["d4"], options, index=None, horizontal=True)
    d5 = st.radio(t["d5"], options, index=None, horizontal=True)
    d6 = st.radio(t["d6"], options, index=None, horizontal=True)
    d7_raw = st.radio(t["d7"], options, index=None, horizontal=True)

    st.divider()
    st.write("**Narrative Reflection (Optional)**")
    d_narrative_1 = st.text_area(t["d_narrative_1"])
    d_narrative_2 = st.text_area(t["d_narrative_2"])

    if st.button(t["btn_continue"], type="primary"):
        st.session_state.responses.update({
            "d1": d1, "d2": d2, "d3": d3, "d4": d4, "d5": d5, "d6": d6, "d7": d7_raw,
            "dep_narrative_1": d_narrative_1, "dep_narrative_2": d_narrative_2
        })
        d_scores = [d1, d2, d3, d4, d5, d6, (6 - d7_raw) if d7_raw is not None else None]
        d_answered = [s for s in d_scores if s is not None]
        st.session_state.responses["deprivation_score_avg"] = sum(d_answered) / len(d_answered) if len(d_answered) > 0 else 0
        
        st.session_state.current_step = 'dmap_part3'
        st.rerun()

# --- PART 3: WAR/CONFLICT ---
elif st.session_state.current_step == 'dmap_part3':
    st.write("---")
    st.header(t["part3_title"])
    st.markdown(t["skip_note"])
    
    options = [1, 2, 3, 4, 5]
    w1 = st.radio(t["w1"], options, index=None, horizontal=True)
    w2 = st.radio(t["w2"], options, index=None, horizontal=True)
    w3 = st.radio(t["w3"], options, index=None, horizontal=True)
    w4 = st.radio(t["w4"], options, index=None, horizontal=True)
    w5 = st.radio(t["w5"], options, index=None, horizontal=True)
    w6 = st.radio(t["w6"], options, index=None, horizontal=True)
    w7_raw = st.radio(t["w7"], options, index=None, horizontal=True)

    if st.button(t["btn_continue"], type="primary"):
        st.session_state.responses.update({"w1": w1, "w2": w2, "w3": w3, "w4": w4, "w5": w5, "w6": w6, "w7": w7_raw})
        w_scores = [w1, w2, w3, w4, w5, w6, (6 - w7_raw) if w7_raw is not None else None]
        w_answered = [s for s in w_scores if s is not None]
        st.session_state.responses["war_score_avg"] = sum(w_answered) / len(w_answered) if len(w_answered) > 0 else 0
        
        st.session_state.current_step = 'cultural_inventory'
        st.rerun()

# --- PART 4: CULTURAL INVENTORY ---
elif st.session_state.current_step == 'cultural_inventory':
    st.write("---")
    st.header(t["part4_title"])
    st.markdown(t["skip_note"])
    
    options = [1, 2, 3, 4, 5]
    c1 = st.radio(t["c1"], options, index=None, horizontal=True)
    c2 = st.radio(t["c2"], options, index=None, horizontal=True)
    c3 = st.radio(t["c3"], options, index=None, horizontal=True)
    c4 = st.radio(t["c4"], options, index=None, horizontal=True)
    c5 = st.radio(t["c5"], options, index=None, horizontal=True)
    c6 = st.radio(t["c6"], options, index=None, horizontal=True)

    if st.button(t["btn_continue"], type="primary"):
        st.session_state.responses.update({"c1_score": c1, "c2_score": c2, "c3_score": c3, "c4_score": c4, "c5_score": c5, "c6_score": c6})
        
        # In this new version, ALL questions C1-C6 lean Collectivist/Interdependent.
        c_scores = [c1, c2, c3, c4, c5, c6]
        c_answered = [s for s in c_scores if s is not None]
        st.session_state.responses["col_score_avg"] = sum(c_answered) / len(c_answered) if len(c_answered) > 0 else 3.0
        
        st.session_state.current_step = 'narrative_recording'
        st.rerun()

# --- PART 5: FINAL NARRATIVE ---
elif st.session_state.current_step == 'narrative_recording':
    st.write("---")
    st.header(t["part5_title"])
    st.markdown(t["skip_note"])

    q1 = st.text_input(t["final_q1"])
    q2 = st.text_input(t["final_q2"])
    q3 = st.text_input(t["final_q3"])

    if st.button(t["btn_continue"], type="primary", use_container_width=True):
        st.session_state.responses.update({
            "final_narrative_1": q1,
            "final_narrative_2": q2,
            "final_narrative_3": q3
        })
        st.session_state.current_step = 'post_gate'
        st.rerun()

# --- POST-ASSESSMENT GATE ---
elif st.session_state.current_step == 'post_gate':
    st.write("---")
    st.subheader(t["post_gate_q"])
    
    if st.button(t["post_gate_fine"], use_container_width=True):
        st.session_state.responses["post_gate_status"] = "Fine"
        st.session_state.current_step = 'decompression'
        st.rerun()
    if st.button(t["post_gate_unsettled"], use_container_width=True):
        st.session_state.responses["post_gate_status"] = "Unsettled"
        st.session_state.current_step = 'decompression'
        st.rerun()
    if st.button(t["post_gate_talk"], use_container_width=True):
        st.session_state.responses["post_gate_status"] = "Requested Support"
        st.session_state.current_step = 'crisis_resources'
        st.rerun()

elif st.session_state.current_step == 'crisis_resources':
    st.write("---")
    st.warning(t["crisis_msg"])
    st.markdown(t["crisis_resources"])
    st.divider()
    if st.button("Submit & Finish Assessment", type="primary"):
        st.session_state.current_step = 'decompression'
        st.rerun()

# --- FINAL DECOMPRESSION / SUBMISSION ---
elif st.session_state.current_step == 'decompression':
    with st.spinner("Processing your responses..."):
        export_data_to_google()
        
    st.success("Thank you. Your responses have been securely recorded.")
    
    if SHOW_RADAR_MAP:
        st.divider()
        t_score = st.session_state.responses.get("threat_score_avg", 0)
        d_score = st.session_state.responses.get("deprivation_score_avg", 0)
        w_score = st.session_state.responses.get("war_score_avg", 0)
        col_score = st.session_state.responses.get("col_score_avg", 3.0)
        
        fig = generate_neurotwin_chart(t_score, d_score, w_score, col_score)
        st.pyplot(fig)
