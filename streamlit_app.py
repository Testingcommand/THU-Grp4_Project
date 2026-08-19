# 6. The Projective Inkblots
elif st.session_state.current_step in ['inkblot_1', 'inkblot_2', 'inkblot_3']:
    
    if st.session_state.current_step == 'inkblot_1':
        # Replaced with a web-safe placeholder!
        image_url = "https://dummyimage.com/800x400/cccccc/000000.png&text=Visual+Scene+1"
        prompt = "What do you see happening in this scene? What are they about to do?"
        scale_label = "How tense or dangerous does this scene feel to you?"
        next_step = 'inkblot_2'
        ai_reply = "Thank you. Let's look at another scene."
        
    elif st.session_state.current_step == 'inkblot_2':
        image_url = "https://dummyimage.com/800x400/cccccc/000000.png&text=Visual+Scene+2"
        prompt = "How do you think resources or rewards are being distributed here?"
        scale_label = "How fair or unfair does this situation feel?"
        next_step = 'inkblot_3'
        ai_reply = "Thank you for sharing your perspective. Let's move to the final image."

    elif st.session_state.current_step == 'inkblot_3':
        image_url = "https://dummyimage.com/800x400/cccccc/000000.png&text=Visual+Scene+3"
        prompt = "Describe the environment. Is it safe, unpredictable, or something else entirely?"
        scale_label = "How unpredictable is this environment?"
        next_step = 'decompression'
        ai_reply = t["decompression_prompt"]

    st.write("---")
    
    # 1. Render the Image
    st.image(image_url, use_container_width=True)
    
    # 2. Render the 1-5 Gamified Slider
    st.markdown(f"### {scale_label}")
    likert_score = st.slider("Scale: 1 (Very Low) to 5 (Very High)", min_value=1, max_value=5, value=3, step=1)
    
    # 3. Render the Narrative Prompt
    st.markdown(f"**{prompt}**")
    
    tab_text, tab_audio = st.tabs([t["tab_text"], t["tab_audio"]])
    
    with tab_text:
        user_text = st.text_area("Type your narrative here:", key=f"text_{st.session_state.current_step}")
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button(t["btn_submit_text"], key=f"btn_txt_{st.session_state.current_step}", type="primary", use_container_width=True):
                if user_text.strip():
                    # Save both the scale score AND the text!
                    st.session_state.responses[f"{st.session_state.current_step}_score"] = likert_score
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
                # Save both the scale score AND the audio!
                st.session_state.responses[f"{st.session_state.current_step}_score"] = likert_score
                audio_path = save_audio_file(audio_bytes, f"{st.session_state.current_step}_audio")
                advance_chat(audio_path, "audio", f"{st.session_state.current_step}_audio", next_step, ai_reply)
