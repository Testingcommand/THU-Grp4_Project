import streamlit as st
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt

# ==========================================
# ADMIN CONFIGURATION
# ==========================================
GOOGLE_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxqdvDAVoXokgjDkHbPLdGzEIdRQ0pGSgbsPukmmD-Rcc8nicwH0KsoRZ8c2P2PdavN/exec"
ADMIN_API_KEY = "NEUROTWIN_RESEARCH_SECRET_KEY_2026" # Ensure this matches Apps Script!

st.set_page_config(page_title="NeuroTwin Clinical Portal", layout="wide")

def fetch_participant_data():
    try:
        res = requests.get(f"{GOOGLE_WEBAPP_URL}?key={ADMIN_API_KEY}", timeout=15)
        if res.status_code == 200:
            return res.json()
        return []
    except Exception:
        return []

def generate_neurotwin_chart(threat_score, deprivation_score, war_score, col_score):
    categories = [
        'Threat Reactivity\n(Amygdala / PAG)', 
        'Social Cognition\n(TPJ / mPFC)', 
        'Reward Sensitivity\n(Ventral Striatum)', 
        'Cognitive Flexibility\n(dlPFC)', 
        'Interoception\n(Insula)'
    ]
    N = len(categories)
    control_scores = [3.0, 3.0, 3.0, 3.0, 3.0] 
    
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

# Functions to command Google Sheets
def set_study_status(is_open):
    status_str = "OPEN" if is_open else "CLOSED"
    payload = {"action": "set_status", "status": status_str, "key": ADMIN_API_KEY}
    try:
        requests.post(GOOGLE_WEBAPP_URL, json=payload)
    except Exception:
        pass

def get_study_status():
    try:
        res = requests.get(f"{GOOGLE_WEBAPP_URL}?action=get_status")
        if res.status_code == 200:
            return res.json().get("is_open", True)
    except Exception:
        return True
    return True

# ==========================================
# DASHBOARD UI & STATUS TOGGLE
# ==========================================
st.title("🛡️ NeuroTwin Secure Clinical Portal")
st.caption("Live Clinical Data Stream • Synchronized with Google Sheets & Drive")

# --- 1. The Visual Toggle Buttons ---
st.subheader("Study Status")
current_status = get_study_status()

if current_status:
    st.success("🟢 The study is currently OPEN to new participants.")
    if st.button("Close Study", type="primary"):
        set_study_status(False)
        st.rerun()
else:
    st.error("🔴 The study is currently CLOSED.")
    if st.button("Reopen Study", type="primary"):
        set_study_status(True)
        st.rerun()
        
st.divider()

# --- 2. Fetch the Data ---
with st.spinner("Fetching latest clinical responses..."):
    data = fetch_participant_data()

if not data:
    st.info("No recorded participant sessions found yet. (Data will appear here once participants submit!)")
    st.stop()

# THIS IS THE MISSING VARIABLE:
df = pd.DataFrame(data)

st.subheader("Submissions Ledger")
st.dataframe(df, use_container_width=True)

csv = df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download Full Study Dataset (CSV)",
    data=csv,
    file_name="neurotwin_study_export.csv",
    mime="text/csv"
)

st.divider()

# ==========================================
# PARTICIPANT PROFILE INSPECTOR
# ==========================================
st.subheader("Individual Clinical Profile & Topology")
# (Now the code knows what 'df' is!)
participant_ids = df["Participant ID"].dropna().unique().tolist()
selected_id = st.selectbox("Select Participant ID to inspect:", ["-- Select ID --"] + participant_ids)

if selected_id != "-- Select ID --":
    p_data = df[df["Participant ID"] == selected_id].iloc[0]
    
    col_chart, col_narrative = st.columns([1, 1])
    
    with col_chart:
        st.write("### Calculated Circuit Topology")
        
        try:
            t_val = float(p_data.get("Threat Avg", 0) or 0)
            d_val = float(p_data.get("Deprivation Avg", 0) or 0)
            w_val = float(p_data.get("War Avg", 0) or 0)
            c_val = float(p_data.get("Collectivism Avg", 3.0) or 3.0)
        except ValueError:
            t_val, d_val, w_val, c_val = 0, 0, 0, 3.0
            
        fig = generate_neurotwin_chart(t_val, d_val, w_val, c_val)
        st.pyplot(fig)
        
        st.info(f"**Threat Index:** {t_val:.2f} | **Deprivation Index:** {d_val:.2f} | **War Index:** {w_val:.2f} | **Collectivism:** {c_val:.2f}")

    with col_narrative:
        st.write("### Narrative & Clinical Reflections")
        
        narratives = {
            "Threat Narrative 1": p_data.get("Threat Narrative 1", ""),
            "Threat Narrative 2": p_data.get("Threat Narrative 2", ""),
            "Deprivation Narrative 1": p_data.get("Deprivation Narrative 1", ""),
            "Deprivation Narrative 2": p_data.get("Deprivation Narrative 2", ""),
            "Childhood Reflection (Change)": p_data.get("Final Narrative 1 (Change)", ""),
            "Identity in One Word": p_data.get("Final Narrative 2 (One Word)", ""),
            "Unsafe Response Mechanism": p_data.get("Final Narrative 3 (Unsafe)", "")
        }
        
        for label, val in narratives.items():
            if val and str(val).strip() and str(val) != "...":
                st.markdown(f"**{label}:**")
                if str(val).startswith("http"):
                    st.markdown(f"🔗 [Open Audio Recording in Google Drive]({val})")
                else:
                    st.write(val)
                    
        st.write("---")
        st.write(f"**Assessment Exit Status:** `{p_data.get('Post-Assessment Status', 'Completed')}`")
        st.write(f"**Primary Language:** `{p_data.get('Language', 'Unknown')}`")
