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
    },
    "Mandarin": {
        "welcome": "欢迎参加叙事语境研究。\n\n您的身心健康对我们很重要。您最近有进食吗？",
        "btn_meal_yes": "是的，我吃过了",
        "btn_meal_no": "没有，最近没吃",
        "meal_yes_reply": "太好了。您现在是否处于一个安全、私密且舒适的环境中来进行反思？",
        "meal_no_reply": "*提示：我们建议您在开始前先吃点零食。*\n\n您现在是否处于一个安全、私密且舒适的环境中？",
        "btn_safe_yes": "是的，我在安全的空间",
        "btn_safe_no": "不在，我需要退出",
        "safe_yes_reply": "谢谢。让我们开始视觉探索。",
        "safe_no_reply": "您的健康是我们的首要任务。我们已安全关闭了您的会话。",
        "decompression_prompt": "感谢您完成这次探索。正在生成您的理论 NeuroTwin 拓扑结构...",
        "tab_text": "⌨️ 输入回复",
        "tab_audio": "🎙️ 录制音频",
        "btn_submit_text": "提交回复",
        "btn_skip": "⏭️ 跳过",
        "error_empty_text": "请在提交前输入回复，或选择“跳过”。",
        "audio_inst_1": "请慢慢来。如果您停下来思考，录音**不会**停止。",
        "audio_inst_2": "**1. 点击麦克风图标一次开始录音。**",
        "audio_inst_3": "**2. 再次点击停止录音并提交。**",
        "audio_inst_4": "⚠️ **重要提示：** 点击停止后，请等待几秒钟让系统处理。",
        "processing_audio": "⏳ 正在处理... 请稍候。",
        "success": "✅ 您的回复已提交。您现在可以关闭此窗口。"
    },
    "Cantonese": {
        "welcome": "歡迎來到敘事語境研究。\n\n你嘅身心健康對我哋好重要。你最近有冇食嘢呀？",
        "btn_meal_yes": "有呀，我食咗喇",
        "btn_meal_no": "冇呀，最近未食",
        "meal_yes_reply": "太好喇。你而家係咪喺一個安全、私密同舒適嘅環境入面進行反思？",
        "meal_no_reply": "*提示：我哋建議你開始之前先食少少嘢。*\n\n你而家係咪喺一個安全、私密同舒適嘅環境入面？",
        "btn_safe_yes": "係，我喺安全嘅空間",
        "btn_safe_no": "唔係，我需要退出",
        "safe_yes_reply": "多謝。等我哋開始視覺探索。",
        "safe_no_reply": "你嘅健康係我哋嘅首要考慮。我哋已經安全咁關閉咗你嘅會話。",
        "decompression_prompt": "多謝你完成呢次探索。緊生成你嘅理論 NeuroTwin 拓撲結構...",
        "tab_text": "⌨️ 輸入回覆",
        "tab_audio": "🎙️ 錄製錄音",
        "btn_submit_text": "提交回覆",
        "btn_skip": "⏭️ 跳過",
        "error_empty_text": "請輸入回覆或選擇「跳過」。",
        "audio_inst_1": "慢慢嚟。如果你停低思考，錄音**唔會**停止。",
        "audio_inst_2": "**1. 㩒一下咪高峰圖標開始錄音。**",
        "audio_inst_3": "**2. 再㩒一次停止錄音並提交。**",
        "audio_inst_4": "⚠️ **重要提示：** 㩒咗停止之後，請等幾秒鐘畀系統處理。",
        "processing_audio": "⏳ 處理緊... 請稍等。",
        "success": "✅ 你嘅回覆已經提交。你而家可以關閉呢個視窗。"
    },
    "Spanish": {
        "welcome": "Bienvenido/a al Estudio de Contexto Narrativo.\n\nSu bienestar es importante para nosotros. ¿Ha comido algo recientemente?",
        "btn_meal_yes": "Sí, he comido",
        "btn_meal_no": "No, no recientemente",
        "meal_yes_reply": "Excelente. ¿Se encuentra actualmente en un entorno seguro, privado y cómodo para reflexionar sobre temas complejos?",
        "meal_no_reply": "*Consejo: Le animamos amablemente a comer un bocadillo antes de comenzar.*\n\n¿Se encuentra actualmente en un entorno seguro, privado y cómodo?",
        "btn_safe_yes": "Sí, estoy en un espacio seguro",
        "btn_safe_no": "No, necesito salir",
        "safe_yes_reply": "Gracias. Comencemos la exploración visual.",
        "safe_no_reply": "Su bienestar es nuestra prioridad. Hemos cerrado su sesión de forma segura.",
        "decompression_prompt": "Gracias por completar este viaje. Generando su topología teórica NeuroTwin...",
        "tab_text": "⌨️ Escribir Respuesta",
        "tab_audio": "🎙️ Grabar Audio",
        "btn_submit_text": "Enviar Respuesta",
        "btn_skip": "⏭️ Omitir",
        "error_empty_text": "Por favor escriba una respuesta o elija 'Omitir'.",
        "audio_inst_1": "Tómese el tiempo que necesite. La grabación **no** se detendrá si hace una pausa.",
        "audio_inst_2": "**1. Haga clic en el micrófono UNA VEZ para comenzar.**",
        "audio_inst_3": "**2. Haga clic una SEGUNDA vez para detener y enviar.**",
        "audio_inst_4": "⚠️ **Importante:** Espere unos segundos para procesar después de detener.",
        "processing_audio": "⏳ Procesando... por favor espere.",
        "success": "✅ Sus respuestas han sido enviadas. Ahora puede cerrar esta ventana."
    },
    "French": {
        "welcome": "Bienvenue dans l'Étude du Contexte Narratif.\n\nVotre bien-être est important pour nous. Avez-vous mangé quelque chose récemment ?",
        "btn_meal_yes": "Oui, j'ai mangé",
        "btn_meal_no": "Non, pas récemment",
        "meal_yes_reply": "Parfait. Êtes-vous dans un environnement sûr, privé et confortable pour réfléchir à des sujets complexes ?",
        "meal_no_reply": "*Conseil : Nous vous encourageons à prendre une collation avant de commencer.*\n\nÊtes-vous dans un environnement sûr et confortable ?",
        "btn_safe_yes": "Oui, je suis dans un espace sûr",
        "btn_safe_no": "Non, je dois quitter",
        "safe_yes_reply": "Merci. Commençons l'exploration visuelle.",
        "safe_no_reply": "Votre bien-être est notre priorité. Nous avons fermé votre session.",
        "decompression_prompt": "Merci d'avoir terminé ce parcours. Génération de votre topologie théorique NeuroTwin...",
        "tab_text": "⌨️ Taper la réponse",
        "tab_audio": "🎙️ Enregistrer l'audio",
        "btn_submit_text": "Soumettre",
        "btn_skip": "⏭️ Passer",
        "error_empty_text": "Veuillez taper une réponse ou choisir 'Passer'.",
        "audio_inst_1": "Prenez votre temps. L'enregistrement **ne s'arrêtera pas** si vous faites une pause.",
        "audio_inst_2": "**1. Cliquez UNE FOIS sur le microphone pour commencer.**",
        "audio_inst_3": "**2. Cliquez une DEUXIÈME fois pour arrêter et soumettre.**",
        "audio_inst_4": "⚠️ **Important :** Patientez quelques secondes après avoir cliqué sur arrêter.",
        "processing_audio": "⏳ Traitement... veuillez patienter.",
        "success": "✅ Vos réponses ont été soumises. Vous pouvez fermer cette fenêtre."
    },
    "Russian": {
        "welcome": "Добро пожаловать в Исследование Нарративного Контекста.\n\nВаше благополучие важно для нас. Вы недавно ели?",
        "btn_meal_yes": "Да, я поел(а)",
        "btn_meal_no": "Нет, недавно не ел(а)",
        "meal_yes_reply": "Отлично. Находитесь ли вы сейчас в безопасной, уединенной и комфортной обстановке?",
        "meal_no_reply": "*Совет: Мы рекомендуем перекусить перед началом.*\n\nВы в безопасной обстановке?",
        "btn_safe_yes": "Да, я в безопасности",
        "btn_safe_no": "Нет, мне нужно выйти",
        "safe_yes_reply": "Спасибо. Давайте начнем визуальное исследование.",
        "safe_no_reply": "Ваше благополучие - наш приоритет. Мы закрыли вашу сессию.",
        "decompression_prompt": "Спасибо. Генерация вашей теоретической топологии NeuroTwin...",
        "tab_text": "⌨️ Напечатать ответ",
        "tab_audio": "🎙️ Записать аудио",
        "btn_submit_text": "Отправить",
        "btn_skip": "⏭️ Пропустить",
        "error_empty_text": "Пожалуйста, введите ответ или выберите 'Пропустить'.",
        "audio_inst_1": "Не торопитесь. Запись **не** остановится, если вы сделаете паузу.",
        "audio_inst_2": "**1. Нажмите на микрофон ОДИН РАЗ, чтобы начать.**",
        "audio_inst_3": "**2. Нажмите ВТОРОЙ РАЗ, чтобы остановить и отправить.**",
        "audio_inst_4": "⚠️ **Важно:** Подождите несколько секунд после остановки.",
        "processing_audio": "⏳ Обработка... пожалуйста, подождите.",
        "success": "✅ Ваши ответы отправлены. Вы можете закрыть это окно."
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

# 1. The Landing Dashboard (IMAGE REMOVED FOR NOW)
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
            st.info("The NeuroTwin instrument uses narrative appraisal to map theoretical brain circuit topologies.")
    with col3:
        if st.button("Consent & Privacy 🔒", use_container_width=True):
            st.info("Your data is strictly confidential and anonymized.")

# 2. Language Selection
elif st.session_state.current_step == 'language_selection':
    st.write("### Please select your preferred language:")
    
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
        
        st.divider()
        st.subheader("Your NeuroTwin Topology")
        st.write("Based on your narrative appraisals, here is a theoretical mapping of your circuit topology against a baseline.")
        
        mock_patient_scores = [4.5, 2.5, 1.5, 2.0, 4.0] 
        fig = generate_neurotwin_chart(mock_patient_scores)
        st.pyplot(fig)
        
    else:
        st.error("⚠️ There was a network issue. A local backup has been safely stored.")
