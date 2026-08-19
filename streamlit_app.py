import streamlit as st

# Configure the app's appearance
st.set_page_config(page_title="DMAP Narrative Instrument", layout="centered")

# Initialize session states
if 'stage' not in st.session_state:
    st.session_state.stage = 'safety_gate'
if 'responses' not in st.session_state:
    st.session_state.responses = {}
if 'modality' not in st.session_state:
    st.session_state.modality = 'text'

# Function to instantly transition between pages (fixes the double-click bug)
def set_stage(new_stage):
    st.session_state.stage = new_stage
    st.rerun()

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
    st.info("When you feel ready and are in a private space, you can return to this link at any time.")
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
    st.write("The following questions explore experiences involving harm or the threat of harm during your developmental years.")
    
    input_label = "Your response:" if st.session_state.modality == 'text' else "Dictate your response (Audio integration placeholder):"
    
    st.write("### 1. Objective Recall")
    st.write("Did you experience instances where you felt physically or emotionally threatened during your childhood? Briefly describe the nature of these events.")
    threat_obj = st.text_area(input_label, value=st.session_state.responses.get('threat_obj', ''), key='t_obj')
    
    st.write("### 2. Subjective Appraisal")
    st.write("How did those specific experiences shape your understanding of safety, and how do they influence your ability to trust others today?")
    threat_subj = st.text_area(input_label, value=st.session_state.responses.get('threat_subj', ''), key='t_subj')
    
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", use_container_width=True):
            # Save data before leaving
            st.session_state.responses['threat_obj'] = st.session_state.t_obj
            st.session_state.responses['threat_subj'] = st.session_state.t_subj
            set_stage('modality_selection')
    with col2:
        if st.button("Next ➡️", use_container_width=True):
            # Save data before leaving
            st.session_state.responses['threat_obj'] = st.session_state.t_obj
            st.session_state.responses['threat_subj'] = st.session_state.t_subj
            set_stage('dmap_deprivation')

# -----------------------------------------
# STAGE 4: DMAP - Deprivation Assessment
# -----------------------------------------
elif st.session_state.stage == 'dmap_deprivation':
    st.title("Part 2: Experiences of Deprivation")
    st.write("The following questions explore experiences involving the absence of expected cognitive, social, or emotional inputs.")
    
    input_label = "Your response:" if st.session_state.modality == 'text' else "Dictate your response (Audio integration placeholder):"
    
    st.write("### 3. Objective Recall")
    st.write("Were there times in your childhood when you felt your basic physical or emotional needs (such as affection, resources, or guidance) were consistently not met?")
    dep_obj = st.text_area(input_label, value=st.session_state.responses.get('dep_obj', ''), key='d_obj')
    
    st.write("### 4. Subjective Appraisal")
    st.write("How has this absence of support or resources influenced how you view your own self-worth and how you connect with communities now?")
    dep_subj = st.text_area(input_label, value=st.session_state.responses.get('dep_subj', ''), key='d_subj')
    
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", use_container_width=True):
            st.session_state.responses['dep_obj'] = st.session_state.d_obj
            st.session_state.responses['dep_subj'] = st.session_state.d_subj
            set_stage('dmap_threat')
    with col2:
        if st.button("Submit Assessment ✅", use_container_width=True):
            st.session_state.responses['dep_obj'] = st.session_state.d_obj
            st.session_state.responses['dep_subj'] = st.session_state.d_subj
            set_stage('decompression')

# -----------------------------------------
# STAGE 5: Decompression & Export
# -----------------------------------------
elif st.session_state.stage == 'decompression':
    st.title("Thank you for sharing your narrative.")
    st.success("Your perspective is vital to building a more context-aware framework for clinical care.")
    st.write("Reflecting on adversity can be challenging. Please take a moment to decompress before closing this application.")
    
    st.markdown("---")
    st.subheader("Raw Data Payload (For AI Backend / Researcher View)")
    st.write("This data will be fed into the NLP sentiment analysis to calculate the divergence score against fMRI results.")
    st.json(st.session_state.responses)
    
    if st.button("⬅️ Back to Editing"):
        set_stage('dmap_deprivation')
