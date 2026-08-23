import streamlit as st
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt

# ==========================================
# ADMIN CONFIGURATION
# ==========================================
GOOGLE_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzsfuk7xO4NLPYD45PKSx5nLr3fTKEDtdIOhOjnCNwqFPndLdujAVRodScyZQU1bFTD/exec"

# These pull securely from Streamlit Cloud Secrets!
ADMIN_API_KEY = st.secrets["admin_api_key"]
TEAM_PASSWORD = st.secrets["team_password"]

st.set_page_config(page_title="NeuroTwin Clinical Portal", layout="wide")

# ==========================================
# PASSWORD LOCKOUT
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Restricted Access")
    st.info("Please enter the research team password to access the clinical portal.")
    pwd_input = st.text_input("Password", type="password")
    if st.button("Login"):
        if pwd_input == TEAM_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop() 

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def fetch_participant_data():
    try:
        res = requests.get(f"{GOOGLE_WEBAPP_URL}?key={ADMIN_API_KEY}", timeout=15)
        if res.status_code == 200:
            return res.json()
        return []
    except Exception:
        return []

def delete_participant_record(participant_id):
    payload = {"action": "delete_participant", "participant_id": participant_id, "key": ADMIN_API_KEY}
    try:
        res = requests.post(GOOGLE_WEBAPP_URL, json=payload, timeout=15, allow_redirects=True)
        return "success" in res.text
    except Exception:
        return False

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

def set_study_status(is_open):
    status_str = "OPEN" if is_open else "CLOSED"
    payload = {"action": "set_status", "status": status_str, "key": ADMIN_API_KEY}
    try:
        res = requests.post(GOOGLE_WEBAPP_URL, json=payload, timeout=15, allow_redirects=True)
        if "success" in res.text:
            return True
        else:
            st.error(f"Google rejected the command: {res.text}")
            return False
    except Exception as e:
        st.error(f"Connection failed: {e}")
        return False

def get_study_status():
    try:
        res = requests.get(f"{GOOGLE_WEBAPP_URL}?action=get_status", timeout=15)
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

col_status, col_refresh = st.columns([3, 1])

with col_status:
    st.subheader("Study Status")
    if "study_is_open" not in st.session_state:
        st.session_state.study_is_open = get_study_status()

    if st.session_state.study_is_open:
        st.success("🟢 The study is currently OPEN to new participants.")
        if st.button("Close Study", type="primary"):
            if set_study_status(False): 
                st.session_state.study_is_open = False
                st.rerun()
    else:
        st.error("🔴 The study is currently CLOSED.")
        if st.button("Reopen Study", type="primary"):
            if set_study_status(True):
                st.session_state.study_is_open = True
                st.rerun()

with col_refresh:
    st.write("") # Spacing
    st.write("") 
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()
        
st.divider()

# ==========================================
# FETCH AND DISPLAY DATA
# ==========================================
with st.spinner("Fetching latest clinical responses..."):
    data = fetch_participant_data()

if not data:
    st.info("No recorded participant sessions found yet. (Data will appear here once participants submit!)")
    st.stop()

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

if "Participant ID" in df.columns:
    participant_ids = df["Participant ID"].dropna().unique().tolist()
else:
    participant_ids = []

selected_id = st.selectbox("Select Participant ID to inspect:", ["-- Select ID --"] + participant_ids)

if selected_id != "-- Select ID --":
    p_data = df[df["Participant ID"] == selected_id].iloc[0]
    
    col_chart, col_narrative = st.columns([1, 1])
    
    with col_chart:
        st.write("### Calculated Circuit Topology")
        
        # Helper function to safely convert to float without crashing
        def safe_float(val, default):
            try:
                return float(val)
            except (ValueError, TypeError):
                return default

        # Safely parse each value INDEPENDENTLY 
        t_val = safe_float(p_data.get("Threat Avg", 0), 0.0)
        d_val = safe_float(p_data.get("Deprivation Avg", 0), 0.0)
        w_val = safe_float(p_data.get("War Avg", 0), 0.0)
        
        # If Collectivism is corrupted (e.g. text), calculate it manually from the raw C1-C6 columns
        try:
            c_val = float(p_data.get("Collectivism Avg", 3.0))
        except (ValueError, TypeError):
            try:
                c_scores = [float(p_data.get(f"C{i}", 3.0)) for i in range(1, 7)]
                c_val = sum(c_scores) / len(c_scores)
            except Exception:
                c_val = 3.0
            
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

    # The Delete Button Section
    st.divider()
    st.warning("⚠️ **Danger Zone**")
    if st.button(f"🗑️ Delete Trial Data for ID: {selected_id}", type="primary"):
        if delete_participant_record(selected_id):
            st.success(f"Successfully deleted {selected_id}. Refreshing the dashboard...")
            st.rerun()
        else:
            st.error("Failed to delete record. Ensure your Google Apps Script is updated and deployed as a New Version.")
