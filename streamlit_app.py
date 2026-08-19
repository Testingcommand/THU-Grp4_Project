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

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

def generate_neurotwin_chart(patient_scores):
    """
    Generates a matplotlib radar chart comparing a patient's theoretical 
    circuit topology against a baseline control.
    """
    # 1. Define the specific neurobiological circuits based on H1-H3
    categories = [
        'Threat Reactivity\n(Amygdala / PAG)',
        'Social Cognition\n(TPJ / mPFC)',
        'Reward Sensitivity\n(Ventral Striatum)',
        'Cognitive Flexibility\n(dlPFC)',
        'Interoception\n(Insula)'
    ]
    N = len(categories)

    # 2. Set up the baseline (control) data
    # Assuming a scale of 1 to 5, where 3 is a standard neurotypical baseline
    control_scores = [3.0, 3.0, 3.0, 3.0, 3.0] 
    
    # We must close the loop for the radar chart by appending the first value to the end
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]
    
    control_scores += control_scores[:1]
    patient_data = patient_scores + patient_scores[:1]

    # 3. Initialize the matplotlib figure
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))

    # 4. Draw one axis per variable and add labels
    plt.xticks(angles[:-1], categories, color='black', size=10)
    ax.set_rlabel_position(0)
    plt.yticks([1, 2, 3, 4, 5], ["1", "2", "3", "4", "5"], color="grey", size=8)
    plt.ylim(0, 5)

    # 5. Plot Control Baseline (The "Expected" Topology)
    ax.plot(angles, control_scores, linewidth=1.5, linestyle='dashed', label='Control Baseline', color='teal')
    ax.fill(angles, control_scores, 'teal', alpha=0.05)

    # 6. Plot Patient NeuroTwin (The "Shifted" Topology)
    ax.plot(angles, patient_data, linewidth=2.5, linestyle='solid', label='Patient NeuroTwin', color='crimson')
    ax.fill(angles, patient_data, 'crimson', alpha=0.25)

    # 7. Add legend and styling
    plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    ax.spines['polar'].set_visible(False) # Softens the outer border
    
    return fig

# --- Streamlit Implementation Example ---
st.title("Interactive NeuroTwin Dashboard")
st.write("Visualizing theoretical circuit topology based on narrative appraisal.")

# Example mapping of how the "Inkblot" test scores would feed into this array.
# Let's assume the user's responses indicated high threat reactivity and low reward sensitivity.
mock_patient_scores = [4.5, 2.5, 1.5, 2.0, 4.0]

# Generate and display the plot
fig = generate_neurotwin_chart(mock_patient_scores)
st.pyplot(fig)

# D. The Projective Inkblot Questions
elif st.session_state.current_step in ['inkblot_1', 'inkblot_2', 'inkblot_3']:
    
    # 1. Define the dynamic content for each image stage
    if st.session_state.current_step == 'inkblot_1':
        # Hypothesis 1 & 2: Social Reading vs. Threat (TPJ / Amygdala)
        image_url = "https://via.placeholder.com/800x400.png?text=[Insert+Ambiguous+Crowd/Social+Image+Here]"
        prompt = "Look at the image above. What do you see happening in this scene? What do you think the individuals are feeling, or what are they about to do?"
        next_step = 'inkblot_2'
        ai_reply = "Thank you. Let's look at another scene."
        
    elif st.session_state.current_step == 'inkblot_2':
        # Hypothesis 3: Reward / Deprivation / Resource Allocation (Ventral Striatum)
        image_url = "https://via.placeholder.com/800x400.png?text=[Insert+Ambiguous+Resource/Task+Image+Here]"
        prompt = "In this image, how do you think resources or rewards are being distributed? What is the core conflict or resolution here?"
        next_step = 'inkblot_3'
        ai_reply = "Thank you for sharing your perspective. Let's move to the final image."

    elif st.session_state.current_step == 'inkblot_3':
        # General Flexibility / Integration (dlPFC)
        image_url = "https://via.placeholder.com/800x400.png?text=[Insert+Abstract+or+Complex+Image+Here]"
        prompt = "Describe the environment in this image. Is it safe, unpredictable, or something else entirely?"
        next_step = 'decompression'
        ai_reply = "Thank you for completing this journey. Your perspective helps us build a more context-aware framework for clinical care. Please wait a moment while I securely save your responses..."

    # 2. Render the Projective Image and Prompt
    st.write("---")
    st.image(image_url, use_column_width=True)
    st.markdown(f"**{prompt}**")
    
    # 3. The Input Tabs (Text vs. Audio)
    tab_text, tab_audio = st.tabs(["⌨️ Type Response", "🎙️ Record Audio"])
    
    with tab_text:
        user_text = st.text_area("Type your narrative here:", key=f"text_{st.session_state.current_step}")
        
        # UI Layout: Submit button next to Skip button
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("Submit Text Response", key=f"btn_txt_{st.session_state.current_step}", type="primary", use_container_width=True):
                if user_text.strip():
                    advance_chat(user_text, "text", f"{st.session_state.current_step}_text", next_step, ai_reply)
                else:
                    st.error("Please type a response or choose 'Skip'.")
        with col2:
            if st.button("⏭️ Skip", key=f"skip_txt_{st.session_state.current_step}", use_container_width=True):
                advance_chat("[User Chose to Skip]", "text", f"{st.session_state.current_step}_skipped", next_step, ai_reply)
                
    with tab_audio:
        st.info("Take all the time you need. The recording will **not** stop if you pause to think.")
        st.markdown("**1. Click the microphone icon ONCE to start recording.**")
        st.markdown("**2. Click it a SECOND time to stop recording and submit.**")
        st.warning("⚠️ **Important:** After clicking stop, please wait a few seconds for your audio to process.")
        
        # UI Layout: Mic next to Skip button
        col3, col4 = st.columns([3, 1])
        with col3:
            audio_bytes = audio_recorder(
                key=f"mic_{st.session_state.current_step}",
                pause_threshold=300.0 
            )
        with col4:
            st.write("") # Spacing alignment
            st.write("")
            if st.button("⏭️ Skip", key=f"skip_aud_{st.session_state.current_step}", use_container_width=True):
                advance_chat("[User Chose to Skip]", "text", f"{st.session_state.current_step}_skipped", next_step, ai_reply)
        
        if audio_bytes:
            with st.spinner("⏳ Processing your recording... please wait a moment."):
                audio_path = save_audio_file(audio_bytes, f"{st.session_state.current_step}_audio")
                advance_chat(audio_path, "audio", f"{st.session_state.current_step}_audio", next_step, ai_reply)

# --- Language Dictionary ---
CONTENT = {
    "English": {
        "welcome": "Welcome to the Narrative Context Study. This instrument explores how early life experiences shape our perspectives.\n\nYour well-being is important to us. Have you had a meal or something to eat recently? (Good health and physical comfort help when reflecting on complex topics).",
        "btn_meal_yes": "Yes, I have eaten",
        "btn_meal_no": "No, not recently",
        "meal_yes_reply": "Great. You are about to be asked questions regarding childhood adversity, threat, and deprivation. Are you currently in a safe, private, and comfortable environment to reflect on these topics?",
        "meal_no_reply": "*Tip: We gently encourage you to grab a snack or some water before beginning.*\n\nYou are about to be asked questions regarding childhood adversity, threat, and deprivation. Are you currently in a safe, private, and comfortable environment to reflect on these topics?",
        "btn_safe_yes": "Yes, I am in a safe space",
        "btn_safe_no": "No, I need to exit",
        "safe_yes_reply": "Thank you. Let's begin Part 1: Experiences of Threat.\n\nDid you experience instances where you felt physically or emotionally threatened during your childhood? Briefly describe the nature of these events.",
        "safe_no_reply": "Your well-being is our priority. It is completely okay to step away. We have securely closed your session.",
        "threat_subj_prompt": "Thank you for sharing that. How did those specific experiences shape your understanding of safety, and how do they influence your ability to trust others today?",
        "dep_obj_prompt": "Part 2: Experiences of Deprivation.\n\nWere there times in your childhood when you felt your basic physical or emotional needs were consistently not met?",
        "dep_subj_prompt": "How has this absence of support or resources influenced how you view your own self-worth and how you connect with communities now?",
        "decompression_prompt": "Thank you for sharing your narrative. Your perspective is vital to building a more context-aware framework for clinical care. Please wait a moment while I securely save your responses...",
        "tab_text": "⌨️ Type Response",
        "tab_audio": "🎙️ Record Audio",
        "btn_submit_text": "Submit Text Response",
        "error_empty_text": "Please type a response before submitting.",
        "audio_inst_1": "Take all the time you need. The recording will **not** stop if you pause to think.",
        "audio_inst_2": "**1. Click the microphone icon ONCE to start recording.**",
        "audio_inst_3": "**2. Click it a SECOND time to stop recording and submit.**",
        "audio_inst_4": "⚠️ **Important:** After clicking stop, please wait a few seconds for your audio to process.",
        "processing_audio": "⏳ Processing your recording... please wait a moment.",
        "upload_warning": "⏳ **Please note:** Uploading your final data to the secure server can take up to a minute depending on your connection. Please do not close or refresh this window until you see the success message below.",
        "success": "✅ Your responses have been successfully and securely submitted. You may now safely close this window.",
        "error_network": "⚠️ There was a network issue saving your response to the cloud. A local backup has been safely stored.",
        "restart_info": "To restart the assessment, please use the button in the sidebar menu on the left.",
        "type_here": "Type your response here..."
    },
    "Mandarin": {
        "welcome": "欢迎参加叙事语境研究。本工具旨在探索早年生活经历如何塑造我们的视角。\n\n您的身心健康对我们很重要。您最近有进食吗？（良好的健康和身体舒适有助于反思复杂的话题）。",
        "btn_meal_yes": "是的，我吃过了",
        "btn_meal_no": "没有，最近没吃",
        "meal_yes_reply": "太好了。接下来将询问有关童年逆境、威胁和匮乏的问题。您现在是否处于一个安全、私密且舒适的环境中来进行反思？",
        "meal_no_reply": "*提示：我们建议您在开始前先吃点零食或喝点水。*\n\n接下来将询问有关童年逆境、威胁和匮乏的问题。您现在是否处于一个安全、私密且舒适的环境中来进行反思？",
        "btn_safe_yes": "是的，我在一个安全的空间",
        "btn_safe_no": "不在，我需要退出",
        "safe_yes_reply": "谢谢。让我们开始第一部分：威胁经历。\n\n在您的童年时期，您是否经历过让您感到身体或情感上受到威胁的情况？请简要描述这些事件的性质。",
        "safe_no_reply": "您的健康是我们的首要任务。您可以随时离开。我们已安全关闭了您的会话。",
        "threat_subj_prompt": "感谢您的分享。这些特定的经历如何塑造了您对安全的理解？它们又如何影响您如今信任他人的能力？",
        "dep_obj_prompt": "第二部分：匮乏经历。\n\n在您的童年时期，是否有过基本生理或情感需求一直未得到满足的时期？",
        "dep_subj_prompt": "这种支持或资源的缺失如何影响了您对自己自我价值的看法，以及您现在如何与社区建立联系？",
        "decompression_prompt": "感谢您分享您的故事。您的观点对于构建更具语境意识的临床护理框架至关重要。请稍候，我正在安全地保存您的回复...",
        "tab_text": "⌨️ 输入回复",
        "tab_audio": "🎙️ 录制音频",
        "btn_submit_text": "提交文本回复",
        "error_empty_text": "请在提交前输入回复。",
        "audio_inst_1": "请慢慢来。如果您停下来思考，录音**不会**停止。",
        "audio_inst_2": "**1. 点击麦克风图标一次开始录音。**",
        "audio_inst_3": "**2. 再次点击停止录音并提交。**",
        "audio_inst_4": "⚠️ **重要提示：** 点击停止后，请等待几秒钟让系统处理您的录音。",
        "processing_audio": "⏳ 正在处理您的录音... 请稍候。",
        "upload_warning": "⏳ **请注意：** 将最终数据上传到安全服务器最多可能需要一分钟。在看到下方的成功提示前，请不要关闭或刷新此窗口。",
        "success": "✅ 您的回复已成功且安全地提交。您现在可以安全地关闭此窗口。",
        "error_network": "⚠️ 将您的回复保存到云端时出现网络问题。本地备份已安全存储。",
        "restart_info": "如需重新开始评估，请使用左侧边栏菜单中的按钮。",
        "type_here": "在此输入您的回复..."
    },
    "Cantonese": {
        "welcome": "歡迎來到敘事語境研究。呢個工具旨在探索早年生活經歷點樣塑造我哋嘅視角。\n\n你嘅身心健康對我哋好重要。你最近有冇食嘢呀？（良好嘅健康同身體舒適有助於反思複雜嘅話題）。",
        "btn_meal_yes": "有呀，我食咗喇",
        "btn_meal_no": "冇呀，最近未食",
        "meal_yes_reply": "太好喇。接下來會問一啲關於童年逆境、威脅同匱乏嘅問題。你而家係咪喺一個安全、私密同舒適嘅環境入面進行反思？",
        "meal_no_reply": "*提示：我哋建議你開始之前先食少少嘢或者飲啲水。*\n\n接下來會問一啲關於童年逆境、威脅同匱乏嘅問題。你而家係咪喺一個安全、私密同舒適嘅環境入面進行反思？",
        "btn_safe_yes": "係，我喺一個安全嘅空間",
        "btn_safe_no": "唔係，我需要退出",
        "safe_yes_reply": "多謝。等我哋開始第一部分：威脅經歷。\n\n喺你嘅童年時期，有冇經歷過令你覺得身體或者情感上受到威脅嘅情況？請簡要描述吓呢啲事件。",
        "safe_no_reply": "你嘅健康係我哋嘅首要考慮。你隨時都可以離開。我哋已經安全咁關閉咗你嘅會話。",
        "threat_subj_prompt": "多謝你嘅分享。嗰啲經歷點樣塑造咗你對安全嘅理解？佢哋又點樣影響你而家信任其他人嘅能力？",
        "dep_obj_prompt": "第二部分：匱乏經歷。\n\n喺你嘅童年時期，有冇一啲時候你覺得基本生理或者情感需求一直都得唔到滿足？",
        "dep_subj_prompt": "呢種支持或資源嘅缺失點樣影響咗你對自己自我價值嘅睇法，同埋你而家點樣同社區建立聯繫？",
        "decompression_prompt": "多謝你分享你嘅故事。你嘅觀點對於構建更具語境意識嘅臨床護理框架非常重要。請稍等，我緊安全咁保存你嘅回覆...",
        "tab_text": "⌨️ 輸入回覆",
        "tab_audio": "🎙️ 錄製錄音",
        "btn_submit_text": "提交文本回覆",
        "error_empty_text": "請喺提交前輸入回覆。",
        "audio_inst_1": "慢慢嚟。如果你停低思考，錄音**唔會**停止。",
        "audio_inst_2": "**1. 㩒一下咪高峰圖標開始錄音。**",
        "audio_inst_3": "**2. 再㩒一次停止錄音並提交。**",
        "audio_inst_4": "⚠️ **重要提示：** 㩒咗停止之後，請等幾秒鐘畀系統處理你嘅錄音。",
        "processing_audio": "⏳ 處理緊你嘅錄音... 請稍等。",
        "upload_warning": "⏳ **請注意：** 將最終數據上傳到安全伺服器最多可能需要一分鐘。喺見到下面嘅成功提示之前，請唔好關閉或刷新呢個視窗。",
        "success": "✅ 你嘅回覆已經成功而且安全咁提交。你而家可以安全咁關閉呢個視窗。",
        "error_network": "⚠️ 將你嘅回覆保存到雲端嗰陣出現網絡問題。本地備份已經安全儲存。",
        "restart_info": "如果想重新開始評估，請用左側邊欄選單入面嘅按鈕。",
        "type_here": "喺度輸入你嘅回覆..."
    },
    "Spanish": {
        "welcome": "Bienvenido/a al Estudio de Contexto Narrativo. Este instrumento explora cómo las experiencias de la vida temprana moldean nuestras perspectivas.\n\nSu bienestar es importante para nosotros. ¿Ha comido algo recientemente? (La buena salud y la comodidad física ayudan al reflexionar sobre temas complejos).",
        "btn_meal_yes": "Sí, he comido",
        "btn_meal_no": "No, no recientemente",
        "meal_yes_reply": "Excelente. A continuación, se le harán preguntas sobre la adversidad infantil, la amenaza y la privación. ¿Se encuentra actualmente en un entorno seguro, privado y cómodo para reflexionar sobre estos temas?",
        "meal_no_reply": "*Consejo: Le animamos amablemente a comer un bocadillo o tomar agua antes de comenzar.*\n\nA continuación, se le harán preguntas sobre la adversidad infantil, la amenaza y la privación. ¿Se encuentra actualmente en un entorno seguro, privado y cómodo para reflexionar sobre estos temas?",
        "btn_safe_yes": "Sí, estoy en un espacio seguro",
        "btn_safe_no": "No, necesito salir",
        "safe_yes_reply": "Gracias. Comencemos la Parte 1: Experiencias de Amenaza.\n\n¿Experimentó situaciones en las que se sintió física o emocionalmente amenazado/a durante su infancia? Describa brevemente la naturaleza de estos eventos.",
        "safe_no_reply": "Su bienestar es nuestra prioridad. Está completamente bien retirarse. Hemos cerrado su sesión de forma segura.",
        "threat_subj_prompt": "Gracias por compartir eso. ¿Cómo moldearon esas experiencias específicas su comprensión de la seguridad y cómo influyen en su capacidad para confiar en los demás hoy en día?",
        "dep_obj_prompt": "Parte 2: Experiencias de Privación.\n\n¿Hubo momentos en su infancia en los que sintió que sus necesidades físicas o emocionales básicas no fueron satisfechas de manera constante?",
        "dep_subj_prompt": "¿Cómo ha influido esta ausencia de apoyo o recursos en cómo ve su propio valor personal y en cómo se conecta con las comunidades ahora?",
        "decompression_prompt": "Gracias por compartir su narrativa. Su perspectiva es vital para construir un marco más consciente del contexto para la atención clínica. Por favor espere un momento mientras guardo de forma segura sus respuestas...",
        "tab_text": "⌨️ Escribir Respuesta",
        "tab_audio": "🎙️ Grabar Audio",
        "btn_submit_text": "Enviar Respuesta",
        "error_empty_text": "Por favor escriba una respuesta antes de enviar.",
        "audio_inst_1": "Tómese todo el tiempo que necesite. La grabación **no** se detendrá si hace una pausa para pensar.",
        "audio_inst_2": "**1. Haga clic en el ícono del micrófono UNA VEZ para comenzar a grabar.**",
        "audio_inst_3": "**2. Haga clic por SEGUNDA vez para detener la grabación y enviarla.**",
        "audio_inst_4": "⚠️ **Importante:** Después de hacer clic en detener, espere unos segundos para que se procese su audio.",
        "processing_audio": "⏳ Procesando su grabación... por favor espere un momento.",
        "upload_warning": "⏳ **Tenga en cuenta:** Subir sus datos finales al servidor seguro puede tardar hasta un minuto dependiendo de su conexión. No cierre ni actualice esta ventana hasta que vea el mensaje de éxito.",
        "success": "✅ Sus respuestas han sido enviadas de forma segura y exitosa. Ahora puede cerrar esta ventana.",
        "error_network": "⚠️ Hubo un problema de red al guardar su respuesta en la nube. Se ha guardado una copia de seguridad local.",
        "restart_info": "Para reiniciar la evaluación, utilice el botón en el menú de la barra lateral a la izquierda.",
        "type_here": "Escriba su respuesta aquí..."
    },
    "French": {
        "welcome": "Bienvenue dans l'Étude du Contexte Narratif. Cet instrument explore comment les expériences de début de vie façonnent nos perspectives.\n\nVotre bien-être est important pour nous. Avez-vous pris un repas ou mangé quelque chose récemment ? (Une bonne santé et un confort physique aident lors de la réflexion sur des sujets complexes).",
        "btn_meal_yes": "Oui, j'ai mangé",
        "btn_meal_no": "Non, pas récemment",
        "meal_yes_reply": "Parfait. Vous allez maintenant répondre à des questions concernant l'adversité infantile, la menace et la privation. Êtes-vous actuellement dans un environnement sûr, privé et confortable pour réfléchir à ces sujets ?",
        "meal_no_reply": "*Conseil : Nous vous encourageons doucement à prendre une collation ou de l'eau avant de commencer.*\n\nVous allez maintenant répondre à des questions concernant l'adversité infantile, la menace et la privation. Êtes-vous actuellement dans un environnement sûr, privé et confortable pour réfléchir à ces sujets ?",
        "btn_safe_yes": "Oui, je suis dans un espace sûr",
        "btn_safe_no": "Non, je dois quitter",
        "safe_yes_reply": "Merci. Commençons la Partie 1 : Expériences de Menace.\n\nAvez-vous vécu des situations où vous vous êtes senti(e) physiquement ou émotionnellement menacé(e) pendant votre enfance ? Décrivez brièvement la nature de ces événements.",
        "safe_no_reply": "Votre bien-être est notre priorité. Il est tout à fait normal de s'arrêter. Nous avons fermé votre session en toute sécurité.",
        "threat_subj_prompt": "Merci d'avoir partagé cela. Comment ces expériences spécifiques ont-elles façonné votre compréhension de la sécurité, et comment influencent-elles votre capacité à faire confiance aux autres aujourd'hui ?",
        "dep_obj_prompt": "Partie 2 : Expériences de Privation.\n\nY a-t-il eu des moments dans votre enfance où vous avez senti que vos besoins physiques ou émotionnels fondamentaux n'étaient pas satisfaits de manière constante ?",
        "dep_subj_prompt": "Comment cette absence de soutien ou de ressources a-t-elle influencé la façon dont vous percevez votre propre valeur et dont vous vous connectez aux communautés maintenant ?",
        "decompression_prompt": "Merci d'avoir partagé votre récit. Votre perspective est vitale pour construire un cadre de soins cliniques plus conscient du contexte. Veuillez patienter un instant pendant que je sauvegarde vos réponses en toute sécurité...",
        "tab_text": "⌨️ Taper la réponse",
        "tab_audio": "🎙️ Enregistrer l'audio",
        "btn_submit_text": "Soumettre la réponse",
        "error_empty_text": "Veuillez taper une réponse avant de soumettre.",
        "audio_inst_1": "Prenez tout le temps dont vous avez besoin. L'enregistrement **ne s'arrêtera pas** si vous faites une pause pour réfléchir.",
        "audio_inst_2": "**1. Cliquez UNE FOIS sur l'icône du microphone pour commencer.**",
        "audio_inst_3": "**2. Cliquez une DEUXIÈME fois pour arrêter l'enregistrement et soumettre.**",
        "audio_inst_4": "⚠️ **Important :** Après avoir cliqué sur arrêter, veuillez patienter quelques secondes pendant le traitement de votre audio.",
        "processing_audio": "⏳ Traitement de votre enregistrement... veuillez patienter.",
        "upload_warning": "⏳ **Veuillez noter :** Le téléchargement de vos données finales vers le serveur peut prendre jusqu'à une minute. Ne fermez pas cette fenêtre avant de voir le message de réussite.",
        "success": "✅ Vos réponses ont été soumises avec succès et en toute sécurité. Vous pouvez maintenant fermer cette fenêtre.",
        "error_network": "⚠️ Il y a eu un problème de réseau lors de l'enregistrement de votre réponse. Une sauvegarde locale a été stockée en toute sécurité.",
        "restart_info": "Pour recommencer l'évaluation, veuillez utiliser le bouton dans le menu latéral à gauche.",
        "type_here": "Tapez votre réponse ici..."
    },
    "Russian": {
        "welcome": "Добро пожаловать в Исследование Нарративного Контекста. Этот инструмент изучает, как ранний жизненный опыт формирует наши взгляды.\n\nВаше благополучие важно для нас. Вы недавно ели? (Хорошее здоровье и физический комфорт помогают при размышлениях на сложные темы).",
        "btn_meal_yes": "Да, я поел(а)",
        "btn_meal_no": "Нет, недавно не ел(а)",
        "meal_yes_reply": "Отлично. Сейчас вам будут заданы вопросы о невзгодах в детстве, угрозах и лишениях. Находитесь ли вы сейчас в безопасной, уединенной и комфортной обстановке, чтобы поразмышлять на эти темы?",
        "meal_no_reply": "*Совет: Мы рекомендуем вам перекусить или выпить воды перед началом.*\n\nСейчас вам будут заданы вопросы о невзгодах в детстве, угрозах и лишениях. Находитесь ли вы сейчас в безопасной, уединенной и комфортной обстановке, чтобы поразмышлять на эти темы?",
        "btn_safe_yes": "Да, я в безопасности",
        "btn_safe_no": "Нет, мне нужно выйти",
        "safe_yes_reply": "Спасибо. Давайте начнем Часть 1: Опыт Угрозы.\n\nПереживали ли вы ситуации, когда чувствовали физическую или эмоциональную угрозу в детстве? Кратко опишите характер этих событий.",
        "safe_no_reply": "Ваше благополучие - наш приоритет. Вы можете прерваться в любой момент. Мы безопасно закрыли вашу сессию.",
        "threat_subj_prompt": "Спасибо, что поделились этим. Как этот конкретный опыт сформировал ваше понимание безопасности, и как он влияет на вашу способность доверять другим людям сегодня?",
        "dep_obj_prompt": "Часть 2: Опыт Лишений.\n\nБыли ли в вашем детстве периоды, когда вы чувствовали, что ваши базовые физические или эмоциональные потребности постоянно не удовлетворялись?",
        "dep_subj_prompt": "Как это отсутствие поддержки или ресурсов повлияло на то, как вы оцениваете собственную значимость и как вы взаимодействуете с обществом сейчас?",
        "decompression_prompt": "Спасибо, что поделились своей историей. Ваша точка зрения жизненно важна для создания более контекстно-ориентированной системы клинической помощи. Пожалуйста, подождите немного, пока я безопасно сохраняю ваши ответы...",
        "tab_text": "⌨️ Напечатать ответ",
        "tab_audio": "🎙️ Записать аудио",
        "btn_submit_text": "Отправить ответ",
        "error_empty_text": "Пожалуйста, введите ответ перед отправкой.",
        "audio_inst_1": "Не торопитесь. Запись **не** остановится, если вы сделаете паузу, чтобы подумать.",
        "audio_inst_2": "**1. Нажмите на значок микрофона ОДИН РАЗ, чтобы начать запись.**",
        "audio_inst_3": "**2. Нажмите ВТОРОЙ РАЗ, чтобы остановить запись и отправить.**",
        "audio_inst_4": "⚠️ **Важно:** После нажатия кнопки «Стоп», пожалуйста, подождите несколько секунд, пока ваше аудио обработается.",
        "processing_audio": "⏳ Обработка вашей записи... пожалуйста, подождите.",
        "upload_warning": "⏳ **Обратите внимание:** Загрузка ваших данных на защищенный сервер может занять до минуты. Пожалуйста, не закрывайте это окно, пока не увидите сообщение об успехе.",
        "success": "✅ Ваши ответы были успешно и безопасно отправлены. Теперь вы можете закрыть это окно.",
        "error_network": "⚠️ При сохранении вашего ответа в облако произошла ошибка сети. Локальная резервная копия сохранена.",
        "restart_info": "Чтобы начать оценку заново, пожалуйста, используйте кнопку в боковом меню слева.",
        "type_here": "Введите ваш ответ здесь..."
    }
}

# --- Initialize Session States ---
if 'responses' not in st.session_state:
    st.session_state.responses = {'id': datetime.now().strftime("%Y%m%d_%H%M%S")}
if 'admin_unlocked' not in st.session_state:
    st.session_state.admin_unlocked = False

# The Chatbot State Machine
if 'current_step' not in st.session_state:
    st.session_state.current_step = 'language_selection'
    st.session_state.messages = []
    st.session_state.lang = "English" # Default placeholder

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
# SIDEBAR: PARTICIPANT CONTROLS & ADMIN
# -----------------------------------------
with st.sidebar:
    st.subheader("Assessment Controls" if st.session_state.lang == "English" else "Controls / 控制")
    if st.button("🔄 Restart / 重新开始 / Reiniciar", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    if st.query_params.get("admin") == "true":
        st.divider()
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
            st.write("🎙️ *Audio Recorded*" if st.session_state.lang == "English" else "🎙️ *Audio*")
            st.audio(msg["content"], format="audio/wav")
        else:
            st.write(msg["content"])

# -----------------------------------------
# STAGE 2: DYNAMIC INPUT HANDLING
# -----------------------------------------

# Retrieve active language dictionary
t = CONTENT[st.session_state.lang]

# A. Language Selection
if st.session_state.current_step == 'language_selection':
    st.write("### Please select your preferred language:")
    st.write("### 请选择您的首选语言：")
    st.write("### Por favor, seleccione su idioma preferido:")
    
    col1, col2, col3 = st.columns(3)
    if col1.button("English", use_container_width=True):
        st.session_state.lang = "English"
        st.session_state.responses['language'] = "English"
        st.session_state.messages.append({"role": "assistant", "type": "text", "content": CONTENT["English"]["welcome"]})
        st.session_state.current_step = 'intro_meal'
        st.rerun()
    if col2.button("中文 (Mandarin)", use_container_width=True):
        st.session_state.lang = "Mandarin"
        st.session_state.responses['language'] = "Mandarin"
        st.session_state.messages.append({"role": "assistant", "type": "text", "content": CONTENT["Mandarin"]["welcome"]})
        st.session_state.current_step = 'intro_meal'
        st.rerun()
    if col3.button("粵語 (Cantonese)", use_container_width=True):
        st.session_state.lang = "Cantonese"
        st.session_state.responses['language'] = "Cantonese"
        st.session_state.messages.append({"role": "assistant", "type": "text", "content": CONTENT["Cantonese"]["welcome"]})
        st.session_state.current_step = 'intro_meal'
        st.rerun()

    col4, col5, col6 = st.columns(3)
    if col4.button("Español (Spanish)", use_container_width=True):
        st.session_state.lang = "Spanish"
        st.session_state.responses['language'] = "Spanish"
        st.session_state.messages.append({"role": "assistant", "type": "text", "content": CONTENT["Spanish"]["welcome"]})
        st.session_state.current_step = 'intro_meal'
        st.rerun()
    if col5.button("Français (French)", use_container_width=True):
        st.session_state.lang = "French"
        st.session_state.responses['language'] = "French"
        st.session_state.messages.append({"role": "assistant", "type": "text", "content": CONTENT["French"]["welcome"]})
        st.session_state.current_step = 'intro_meal'
        st.rerun()
    if col6.button("Русский (Russian)", use_container_width=True):
        st.session_state.lang = "Russian"
        st.session_state.responses['language'] = "Russian"
        st.session_state.messages.append({"role": "assistant", "type": "text", "content": CONTENT["Russian"]["welcome"]})
        st.session_state.current_step = 'intro_meal'
        st.rerun()

# B. Meal Check
elif st.session_state.current_step == 'intro_meal':
    col1, col2 = st.columns(2)
    if col1.button(t["btn_meal_yes"], use_container_width=True):
        advance_chat(t["btn_meal_yes"], "text", "has_eaten", "safety_gate", t["meal_yes_reply"])
    if col2.button(t["btn_meal_no"], use_container_width=True):
        advance_chat(t["btn_meal_no"], "text", "has_eaten", "safety_gate", t["meal_no_reply"])

# C. Safety Gate
elif st.session_state.current_step == 'safety_gate':
    col1, col2 = st.columns(2)
    if col1.button(t["btn_safe_yes"], use_container_width=True):
        advance_chat(t["btn_safe_yes"], "text", "safe_space", "threat_obj", t["safe_yes_reply"])
    if col2.button(t["btn_safe_no"], use_container_width=True):
        advance_chat(t["btn_safe_no"], "text", "safe_space", "safe_exit", t["safe_no_reply"])

# D. Exit Gate
elif st.session_state.current_step == 'safe_exit':
    st.info(t["restart_info"])

# E. The Core DMAP Questions (Tabbed Interface)
elif st.session_state.current_step in ['threat_obj', 'threat_subj', 'dep_obj', 'dep_subj']:
    
    if st.session_state.current_step == 'threat_obj':
        next_step = 'threat_subj'
        ai_reply = t["threat_subj_prompt"]
    elif st.session_state.current_step == 'threat_subj':
        next_step = 'dep_obj'
        ai_reply = t["dep_obj_prompt"]
    elif st.session_state.current_step == 'dep_obj':
        next_step = 'dep_subj'
        ai_reply = t["dep_subj_prompt"]
    elif st.session_state.current_step == 'dep_subj':
        next_step = 'decompression'
        ai_reply = t["decompression_prompt"]

    st.write("---")
    
    tab_text, tab_audio = st.tabs([t["tab_text"], t["tab_audio"]])
    
    with tab_text:
        user_text = st.text_area(t["type_here"], key=f"text_{st.session_state.current_step}")
        if st.button(t["btn_submit_text"], key=f"btn_txt_{st.session_state.current_step}", type="primary"):
            if user_text.strip():
                advance_chat(user_text, "text", f"{st.session_state.current_step}_text", next_step, ai_reply)
            else:
                st.error(t["error_empty_text"])
                
    with tab_audio:
        st.info(t["audio_inst_1"])
        st.markdown(t["audio_inst_2"])
        st.markdown(t["audio_inst_3"])
        st.warning(t["audio_inst_4"])
        
        audio_bytes = audio_recorder(
            key=f"mic_{st.session_state.current_step}",
            pause_threshold=300.0 
        )
        
        if audio_bytes:
            with st.spinner(t["processing_audio"]):
                audio_path = save_audio_file(audio_bytes, f"{st.session_state.current_step}_audio")
                advance_chat(audio_path, "audio", f"{st.session_state.current_step}_audio", next_step, ai_reply)

# F. Decompression & Export
elif st.session_state.current_step == 'decompression':
    st.info(t["upload_warning"])
    with st.spinner(t["processing_audio"]):
        success = export_data_to_google()
        save_data_to_json() 
        
    if success:
        st.success(t["success"])
    else:
        st.error(t["error_network"])
