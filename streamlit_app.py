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
    categories = [
        'Threat Reactivity\n(Amygdala / PAG)',
        'Social Cognition\n(TPJ / mPFC)',
        'Reward Sensitivity\n(Ventral Striatum)',
        'Cognitive Flexibility\n(dlPFC)',
        'Interoception\n(Insula)'
    ]
    N = len(categories)
    
    control_scores = [3.0, 3.0, 3.0, 3.0, 3.0] 
    
    patient_scores = [
        threat_score,           
        3.0,                    
        deprivation_score,      
        deprivation_score,      
        threat_score            
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
        "success": "✅ Your responses have been submitted. You may now close this window.",
        
        "inv_title": "The DMAP Narrative Inventory",
        "inv_citation": "*Adapted from https://psytests.org/result?v=aceqLWU1V&b=52Zz47bBJD503*",
        "scale_desc": "**Scale:** `1=Never true` | `2=Rarely true` | `3=Sometimes true` | `4=Often true` | `5=Very often true`",
        "part1_title": "Part 1: Indicators of Threat",
        "part1_desc": "This section targets experiences that theoretically upregulate fear-learning circuits and threat vigilance.",
        "t1": "T1: I felt a constant need to be on guard or 'walk on eggshells' in my own home.",
        "t2": "T2: Adults in my life used intense anger, fear, or intimidation to control my behavior.",
        "t3": "T3: I witnessed aggressive physical or verbal conflicts between people in my household.",
        "t4": "T4: My environment felt unpredictable; I never knew what mood my caretakers would be in.",
        "t5": "T5: I was subjected to physical discipline that felt excessive, unsafe, or unpredictable.",
        "t6": "T6: People I depended on made me feel physically or emotionally unsafe.",
        "t7": "T7 (Reverse): When I made a mistake, I trusted that I would be corrected gently rather than harshly.",
        "part2_title": "Part 2: Indicators of Deprivation",
        "part2_desc": "This section targets the absence of expected cognitive, social, or material inputs.",
        "d1": "D1: I went long periods without adults asking about my thoughts, feelings, or interests.",
        "d2": "D2: My home lacked engaging things to do, such as books to read, toys, or access to hobbies.",
        "d3": "D3: I often had to worry about whether our basic needs (like enough food, electricity, or stable housing) would be met.",
        "d4": "D4: I was frequently left alone or unsupervised for longer than was appropriate for my age.",
        "d5": "D5: It was rare for adults in my life to offer praise, encouragement, or affection.",
        "d6": "D6: I did not have an adult who reliably helped me with schoolwork or taught me new skills.",
        "d7": "D7 (Reverse): My home environment felt mentally stimulating and full of opportunities to learn.",
        "part3_title": "Part 3: Narrative Context (Optional)",
        "part3_desc": "**How did these experiences shape how you view the world today? Please feel free to share a specific memory or reflection.**"
    },
    "Mandarin": {
        "welcome": "欢迎参加叙事语境研究。\n\n您的身心健康对我们很重要。您最近有进食吗？",
        "btn_meal_yes": "是的，我吃过了",
        "btn_meal_no": "没有，最近没吃",
        "meal_yes_reply": "太好了。您现在是否处于一个安全、私密且舒适的环境中来进行反思？",
        "meal_no_reply": "*提示：我们建议您在开始前先吃点零食。*\n\n您现在是否处于一个安全、私密且舒适的环境中？",
        "btn_safe_yes": "是的，我在安全的空间",
        "btn_safe_no": "不在，我需要退出",
        "safe_yes_reply": "谢谢。让我们开始评估。",
        "safe_no_reply": "您的健康是我们的首要任务。我们已安全关闭了您的会话。",
        "decompression_prompt": "感谢您完成本问卷。正在生成您的理论 NeuroTwin 拓扑结构...",
        "tab_text": "⌨️ 输入回复",
        "tab_audio": "🎙️ 录制音频",
        "btn_submit_text": "提交评估",
        "btn_skip": "⏭️ 跳过叙述",
        "error_empty_text": "请在提交前输入回复，或选择“跳过”。",
        "audio_inst_1": "请慢慢来。如果您停下来思考，录音**不会**停止。",
        "audio_inst_2": "**1. 点击麦克风图标一次开始录音。**",
        "audio_inst_3": "**2. 再次点击停止录音并提交。**",
        "audio_inst_4": "⚠️ **重要提示：** 点击停止后，请等待几秒钟让系统处理。",
        "processing_audio": "⏳ 正在处理... 请稍候。",
        "success": "✅ 您的回复已提交。您现在可以关闭此窗口。",

        "inv_title": "DMAP 叙事问卷",
        "inv_citation": "*改编自 https://psytests.org/result?v=aceqLWU1V&b=52Zz47bBJD503*",
        "scale_desc": "**评分表:** `1=从不` | `2=很少` | `3=有时` | `4=经常` | `5=总是`",
        "part1_title": "第一部分：威胁指标",
        "part1_desc": "本部分针对理论上会增强恐惧学习回路和威胁警觉性的经历。",
        "t1": "T1: 在自己家里，我感到需要时刻保持警惕或如履薄冰。",
        "t2": "T2: 生活中的成年人使用强烈的愤怒、恐惧或恐吓来控制我的行为。",
        "t3": "T3: 我目睹了家庭成员之间激烈的身体或言语冲突。",
        "t4": "T4: 我的环境感觉不可预测；我永远不知道照顾我的人会是什么心情。",
        "t5": "T5: 我遭受过感觉过度、不安全或不可预测的身体惩罚。",
        "t6": "T6: 我依赖的人让我感到身体或情感上不安全。",
        "t7": "T7 (反向评分): 当我犯错时，我相信自己会得到温和的纠正，而不是严厉的惩罚。",
        "part2_title": "第二部分：匮乏指标",
        "part2_desc": "本部分针对预期认知、社交或物质投入的缺失。",
        "d1": "D1: 我很长一段时间没有成年人询问我的想法、感受或兴趣。",
        "d2": "D2: 我家里缺乏吸引人的东西，比如要读的书、玩具或爱好。",
        "d3": "D3: 我经常不得不担心我们的基本需求（如充足的食物、电或稳定的住房）是否能得到满足。",
        "d4": "D4: 我经常被单独留下或无人看管，时间超过了我这个年龄应有的限度。",
        "d5": "D5: 生活中的成年人很少给予赞扬、鼓励或喜爱。",
        "d6": "D6: 我没有一个成年人能可靠地帮助我做功课或教我新技能。",
        "d7": "D7 (反向评分): 我的家庭环境让人感到精神上的刺激，充满了学习的机会。",
        "part3_title": "第三部分：叙事背景（可选）",
        "part3_desc": "**这些经历如何塑造了您今天看待世界的方式？请随时分享具体的记忆或感想。**"
    },
    "Cantonese": {
        "welcome": "歡迎來到敘事語境研究。\n\n你嘅身心健康對我哋好重要。你最近有冇食嘢呀？",
        "btn_meal_yes": "有呀，我食咗喇",
        "btn_meal_no": "冇呀，最近未食",
        "meal_yes_reply": "太好喇。你而家係咪喺一個安全、私密同舒適嘅環境入面進行反思？",
        "meal_no_reply": "*提示：我哋建議你開始之前先食少少嘢。*\n\n你而家係咪喺一個安全、私密同舒適嘅環境入面？",
        "btn_safe_yes": "係，我喺安全嘅空間",
        "btn_safe_no": "唔係，我需要退出",
        "safe_yes_reply": "多謝。等我哋開始評估。",
        "safe_no_reply": "你嘅健康係我哋嘅首要考慮。我哋已經安全咁關閉咗你嘅會話。",
        "decompression_prompt": "多謝你完成呢份問卷。緊生成你嘅理論 NeuroTwin 拓撲結構...",
        "tab_text": "⌨️ 輸入回覆",
        "tab_audio": "🎙️ 錄製錄音",
        "btn_submit_text": "提交評估",
        "btn_skip": "⏭️ 跳過敘述",
        "error_empty_text": "請輸入回覆或選擇「跳過」。",
        "audio_inst_1": "慢慢嚟。如果你停低思考，錄音**唔會**停止。",
        "audio_inst_2": "**1. 㩒一下咪高峰圖標開始錄音。**",
        "audio_inst_3": "**2. 再㩒一次停止錄音並提交。**",
        "audio_inst_4": "⚠️ **重要提示：** 㩒咗停止之後，請等幾秒鐘畀系統處理。",
        "processing_audio": "⏳ 處理緊... 請稍等。",
        "success": "✅ 你嘅回覆已經提交。你而家可以關閉呢個視窗。",

        "inv_title": "DMAP 敘事問卷",
        "inv_citation": "*改編自 https://psytests.org/result?v=aceqLWU1V&b=52Zz47bBJD503*",
        "scale_desc": "**評分表:** `1=從來唔係` | `2=好少` | `3=有時` | `4=經常` | `5=一直都係`",
        "part1_title": "第一部分：威脅指標",
        "part1_desc": "呢部分針對理論上會增強恐懼學習同威脅警覺性嘅經歷。",
        "t1": "T1: 喺自己屋企，我會覺得需要時刻保持警惕或者步步為營。",
        "t2": "T2: 生活中嘅成年人會用強烈嘅憤怒、恐懼或者恐嚇嚟控制我。",
        "t3": "T3: 我見過屋企人之間有激烈嘅身體或者言語衝突。",
        "t4": "T4: 我嘅環境感覺好難預測；我永遠唔知照顧我嘅人會有咩心情。",
        "t5": "T5: 我受過覺得過度、唔安全或者難以預料嘅體罰。",
        "t6": "T6: 我依賴嘅人令我喺身體或者情感上覺得唔安全。",
        "t7": "T7 (反向評分): 當我做錯事，我信自己會得到溫和嘅教導，而唔係嚴厲嘅懲罰。",
        "part2_title": "第二部分：匱乏指標",
        "part2_desc": "呢部分針對預期認知、社交或物質投入嘅缺失。",
        "d1": "D1: 我好長一段時間冇成年人問過我嘅想法、感受或者興趣。",
        "d2": "D2: 我屋企冇吸引人嘅嘢做，好似睇書、玩玩具或者培養愛好。",
        "d3": "D3: 我成日要擔心我哋嘅基本需求（例如夠唔夠食物、水電或者穩定住處）得唔得到滿足。",
        "d4": "D4: 我成日俾人單獨留低或者無人睇管，時間超過咗我呢個年紀應有嘅限度。",
        "d5": "D5: 生活中嘅成年人好少會讚我、鼓勵我或者錫我。",
        "d6": "D6: 我冇一個成年人可以可靠咁幫我做功課或者教我新嘢。",
        "d7": "D7 (反向評分): 我嘅家庭環境令人覺得有精神上嘅刺激，充滿學習機會。",
        "part3_title": "第三部分：敘事背景（可選）",
        "part3_desc": "**呢啲經歷點樣塑造咗你今日睇世界嘅方式？請隨便分享具體嘅記憶或者感想。**"
    },
    "Spanish": {
        "welcome": "Bienvenido/a al Estudio de Contexto Narrativo.\n\nSu bienestar es importante para nosotros. ¿Ha comido algo recientemente?",
        "btn_meal_yes": "Sí, he comido",
        "btn_meal_no": "No, no recientemente",
        "meal_yes_reply": "Excelente. ¿Se encuentra actualmente en un entorno seguro, privado y cómodo para reflexionar sobre temas complejos?",
        "meal_no_reply": "*Consejo: Le animamos amablemente a comer un bocadillo antes de comenzar.*\n\n¿Se encuentra en un entorno seguro, privado y cómodo?",
        "btn_safe_yes": "Sí, estoy en un espacio seguro",
        "btn_safe_no": "No, necesito salir",
        "safe_yes_reply": "Gracias. Comencemos el inventario DMAP.",
        "safe_no_reply": "Su bienestar es nuestra prioridad. Hemos cerrado su sesión.",
        "decompression_prompt": "Gracias por completar este inventario. Generando su topología teórica NeuroTwin...",
        "tab_text": "⌨️ Escribir Respuesta",
        "tab_audio": "🎙️ Grabar Audio",
        "btn_submit_text": "Enviar Evaluación",
        "btn_skip": "⏭️ Omitir Narrativa",
        "error_empty_text": "Por favor escriba una respuesta o elija 'Omitir'.",
        "audio_inst_1": "Tómese el tiempo que necesite. La grabación **no** se detendrá si hace una pausa.",
        "audio_inst_2": "**1. Haga clic en el micrófono UNA VEZ para comenzar.**",
        "audio_inst_3": "**2. Haga clic una SEGUNDA vez para detener y enviar.**",
        "audio_inst_4": "⚠️ **Importante:** Espere unos segundos para procesar después de detener.",
        "processing_audio": "⏳ Procesando... por favor espere.",
        "success": "✅ Sus respuestas han sido enviadas. Ahora puede cerrar esta ventana.",

        "inv_title": "El Inventario Narrativo DMAP",
        "inv_citation": "*Adaptado de https://psytests.org/result?v=aceqLWU1V&b=52Zz47bBJD503*",
        "scale_desc": "**Escala:** `1=Nunca` | `2=Raramente` | `3=A veces` | `4=A menudo` | `5=Muy a menudo`",
        "part1_title": "Parte 1: Indicadores de Amenaza",
        "part1_desc": "Esta sección aborda experiencias que aumentan la vigilancia ante amenazas.",
        "t1": "T1: Sentía la necesidad constante de estar en guardia en mi propia casa.",
        "t2": "T2: Los adultos en mi vida usaban ira intensa, miedo o intimidación para controlarme.",
        "t3": "T3: Fui testigo de agresiones físicas o verbales entre personas en mi hogar.",
        "t4": "T4: Mi entorno se sentía impredecible; nunca sabía de qué humor estarían mis cuidadores.",
        "t5": "T5: Fui sometido/a a disciplina física que sentí excesiva o insegura.",
        "t6": "T6: Las personas de las que dependía me hacían sentir inseguro/a física o emocionalmente.",
        "t7": "T7 (Inverso): Cuando cometía un error, confiaba en que me corregirían con suavidad.",
        "part2_title": "Parte 2: Indicadores de Privación",
        "part2_desc": "Esta sección aborda la ausencia de estímulos cognitivos, sociales o materiales.",
        "d1": "D1: Pasaba largos períodos sin que los adultos preguntaran sobre mis sentimientos o intereses.",
        "d2": "D2: A mi hogar le faltaban cosas interesantes para hacer, como libros o juguetes.",
        "d3": "D3: A menudo tenía que preocuparme de si se cubrirían nuestras necesidades básicas (comida, electricidad).",
        "d4": "D4: Con frecuencia me dejaban solo/a o sin supervisión más tiempo del apropiado para mi edad.",
        "d5": "D5: Era raro que los adultos en mi vida me ofrecieran elogios, ánimo o afecto.",
        "d6": "D6: No tenía un adulto que me ayudara con la tarea escolar o me enseñara nuevas habilidades.",
        "d7": "D7 (Inverso): Mi entorno familiar se sentía mentalmente estimulante.",
        "part3_title": "Parte 3: Contexto Narrativo (Opcional)",
        "part3_desc": "**¿Cómo moldearon estas experiencias su visión del mundo? Por favor, comparta un recuerdo o reflexión.**"
    },
    "French": {
        "welcome": "Bienvenue dans l'Étude du Contexte Narratif.\n\nVotre bien-être est important pour nous. Avez-vous mangé quelque chose récemment ?",
        "btn_meal_yes": "Oui, j'ai mangé",
        "btn_meal_no": "Non, pas récemment",
        "meal_yes_reply": "Parfait. Êtes-vous dans un environnement sûr, privé et confortable pour réfléchir ?",
        "meal_no_reply": "*Conseil : Nous vous encourageons à prendre une collation avant de commencer.*\n\nÊtes-vous dans un environnement sûr et confortable ?",
        "btn_safe_yes": "Oui, je suis dans un espace sûr",
        "btn_safe_no": "Non, je dois quitter",
        "safe_yes_reply": "Merci. Commençons l'inventaire DMAP.",
        "safe_no_reply": "Votre bien-être est notre priorité. Nous avons fermé votre session.",
        "decompression_prompt": "Merci d'avoir terminé cet inventaire. Génération de votre topologie théorique NeuroTwin...",
        "tab_text": "⌨️ Taper la réponse",
        "tab_audio": "🎙️ Enregistrer l'audio",
        "btn_submit_text": "Soumettre l'évaluation",
        "btn_skip": "⏭️ Passer la narration",
        "error_empty_text": "Veuillez taper une réponse ou choisir 'Passer'.",
        "audio_inst_1": "Prenez votre temps. L'enregistrement **ne s'arrêtera pas** si vous faites une pause.",
        "audio_inst_2": "**1. Cliquez UNE FOIS sur le microphone pour commencer.**",
        "audio_inst_3": "**2. Cliquez une DEUXIÈME fois pour arrêter et soumettre.**",
        "audio_inst_4": "⚠️ **Important :** Patientez quelques secondes après avoir cliqué sur arrêter.",
        "processing_audio": "⏳ Traitement... veuillez patienter.",
        "success": "✅ Vos réponses ont été soumises. Vous pouvez fermer cette fenêtre.",

        "inv_title": "L'Inventaire Narratif DMAP",
        "inv_citation": "*Adapté de https://psytests.org/result?v=aceqLWU1V&b=52Zz47bBJD503*",
        "scale_desc": "**Échelle:** `1=Jamais` | `2=Rarement` | `3=Parfois` | `4=Souvent` | `5=Très souvent`",
        "part1_title": "Partie 1 : Indicateurs de Menace",
        "part1_desc": "Cette section cible les expériences qui augmentent la vigilance aux menaces.",
        "t1": "T1: Je ressentais un besoin constant d'être sur mes gardes dans ma propre maison.",
        "t2": "T2: Les adultes de ma vie utilisaient une colère intense ou l'intimidation pour me contrôler.",
        "t3": "T3: J'ai été témoin de conflits physiques ou verbaux agressifs dans mon foyer.",
        "t4": "T4: Mon environnement me semblait imprévisible ; je ne savais jamais de quelle humeur seraient les adultes.",
        "t5": "T5: J'ai subi une discipline physique qui me semblait excessive, dangereuse ou imprévisible.",
        "t6": "T6: Les personnes dont je dépendais me faisaient me sentir physiquement ou émotionnellement en insécurité.",
        "t7": "T7 (Inversé): Quand je faisais une erreur, je savais que je serais corrigé(e) doucement plutôt que durement.",
        "part2_title": "Partie 2 : Indicateurs de Privation",
        "part2_desc": "Cette section cible l'absence d'apports cognitifs, sociaux ou matériels.",
        "d1": "D1: Je passais de longues périodes sans que les adultes ne s'intéressent à mes pensées ou mes sentiments.",
        "d2": "D2: Ma maison manquait de choses stimulantes à faire, comme des livres à lire ou des jouets.",
        "d3": "D3: Je devais souvent m'inquiéter de savoir si nos besoins fondamentaux (nourriture, électricité) seraient satisfaits.",
        "d4": "D4: J'étais fréquemment laissé(e) seul(e) ou sans surveillance plus longtemps qu'il n'était approprié pour mon âge.",
        "d5": "D5: Il était rare que les adultes de ma vie m'offrent des éloges, des encouragements ou de l'affection.",
        "d6": "D6: Je n'avais pas d'adulte qui m'aidait de manière fiable pour mes devoirs ou m'apprenait de nouvelles compétences.",
        "d7": "D7 (Inversé): Mon environnement familial me semblait mentalement stimulant.",
        "part3_title": "Partie 3 : Contexte Narratif (Optionnel)",
        "part3_desc": "**Comment ces expériences ont-elles façonné votre vision du monde aujourd'hui ? N'hésitez pas à partager un souvenir.**"
    },
    "Russian": {
        "welcome": "Добро пожаловать в Исследование Нарративного Контекста.\n\nВаше благополучие важно для нас. Вы недавно ели?",
        "btn_meal_yes": "Да, я поел(а)",
        "btn_meal_no": "Нет, недавно не ел(а)",
        "meal_yes_reply": "Отлично. Находитесь ли вы сейчас в безопасной, уединенной и комфортной обстановке?",
        "meal_no_reply": "*Совет: Мы рекомендуем перекусить перед началом.*\n\nВы в безопасной обстановке?",
        "btn_safe_yes": "Да, я в безопасности",
        "btn_safe_no": "Нет, мне нужно выйти",
        "safe_yes_reply": "Спасибо. Давайте начнем инвентаризацию DMAP.",
        "safe_no_reply": "Ваше благополучие - наш приоритет. Мы закрыли вашу сессию.",
        "decompression_prompt": "Спасибо. Генерация вашей теоретической топологии NeuroTwin...",
        "tab_text": "⌨️ Напечатать ответ",
        "tab_audio": "🎙️ Записать аудио",
        "btn_submit_text": "Отправить оценку",
        "btn_skip": "⏭️ Пропустить историю",
        "error_empty_text": "Пожалуйста, введите ответ или выберите 'Пропустить'.",
        "audio_inst_1": "Не торопитесь. Запись **не** остановится, если вы сделаете паузу.",
        "audio_inst_2": "**1. Нажмите на микрофон ОДИН РАЗ, чтобы начать.**",
        "audio_inst_3": "**2. Нажмите ВТОРОЙ РАЗ, чтобы остановить и отправить.**",
        "audio_inst_4": "⚠️ **Важно:** Подождите несколько секунд после остановки.",
        "processing_audio": "⏳ Обработка... пожалуйста, подождите.",
        "success": "✅ Ваши ответы отправлены. Вы можете закрыть это окно.",

        "inv_title": "Нарративный Опросник DMAP",
        "inv_citation": "*Адаптировано из https://psytests.org/result?v=aceqLWU1V&b=52Zz47bBJD503*",
        "scale_desc": "**Шкала:** `1=Никогда` | `2=Редко` | `3=Иногда` | `4=Часто` | `5=Очень часто`",
        "part1_title": "Часть 1: Индикаторы Угрозы",
        "part1_desc": "Этот раздел посвящен опыту, который повышает бдительность к угрозам.",
        "t1": "T1: Я чувствовал(а) постоянную необходимость быть начеку в собственном доме.",
        "t2": "T2: Взрослые использовали сильный гнев, страх или запугивание, чтобы контролировать меня.",
        "t3": "T3: Я был(а) свидетелем агрессивных физических или словесных конфликтов в семье.",
        "t4": "T4: Моя среда казалась непредсказуемой; я никогда не знал(а), в каком настроении будут взрослые.",
        "t5": "T5: Я подвергался(-ась) физическим наказаниям, которые казались чрезмерными или небезопасными.",
        "t6": "T6: Люди, от которых я зависел(а), заставляли меня чувствовать себя физически или эмоционально небезопасно.",
        "t7": "T7 (Обратная шкала): Когда я совершал(а) ошибку, я верил(а), что меня поправят мягко, а не грубо.",
        "part2_title": "Часть 2: Индикаторы Лишений",
        "part2_desc": "Этот раздел посвящен отсутствию когнитивной, социальной или материальной поддержки.",
        "d1": "D1: Взрослые подолгу не спрашивали о моих мыслях, чувствах или интересах.",
        "d2": "D2: В моем доме не было интересных занятий, таких как книги или игрушки.",
        "d3": "D3: Мне часто приходилось беспокоиться о том, будут ли удовлетворены наши базовые потребности (еда, электричество).",
        "d4": "D4: Меня часто оставляли одного/одну без присмотра дольше, чем это было приемлемо для моего возраста.",
        "d5": "D5: Взрослые редко хвалили, поощряли или проявляли привязанность ко мне.",
        "d6": "D6: У меня не было взрослого, который бы надежно помогал мне с уроками или учил новым навыкам.",
        "d7": "D7 (Обратная шкала): Моя домашняя обстановка была умственно стимулирующей.",
        "part3_title": "Часть 3: Нарративный Контекст (Необязательно)",
        "part3_desc": "**Как этот опыт сформировал то, как вы видите мир сегодня? Пожалуйста, поделитесь воспоминанием.**"
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

# THE DMAP INVENTORY MODULE (No Auto-Select + Citation)
elif st.session_state.current_step == 'dmap_inventory':
    st.write("---")
    st.header(t["inv_title"])
    st.markdown(t["inv_citation"])
    st.markdown(t["scale_desc"])
    
    # DIMENSION 1: THREAT
    st.subheader(t["part1_title"])
    st.info(t["part1_desc"])
    options = [1, 2, 3, 4, 5]
    
    t1 = st.radio(t["t1"], options, index=None, horizontal=True)
    t2 = st.radio(t["t2"], options, index=None, horizontal=True)
    t3 = st.radio(t["t3"], options, index=None, horizontal=True)
    t4 = st.radio(t["t4"], options, index=None, horizontal=True)
    t5 = st.radio(t["t5"], options, index=None, horizontal=True)
    t6 = st.radio(t["t6"], options, index=None, horizontal=True)
    t7_raw = st.radio(t["t7"], options, index=None, horizontal=True)

    st.divider()

    # DIMENSION 2: DEPRIVATION
    st.subheader(t["part2_title"])
    st.info(t["part2_desc"])
    
    d1 = st.radio(t["d1"], options, index=None, horizontal=True)
    d2 = st.radio(t["d2"], options, index=None, horizontal=True)
    d3 = st.radio(t["d3"], options, index=None, horizontal=True)
    d4 = st.radio(t["d4"], options, index=None, horizontal=True)
    d5 = st.radio(t["d5"], options, index=None, horizontal=True)
    d6 = st.radio(t["d6"], options, index=None, horizontal=True)
    d7_raw = st.radio(t["d7"], options, index=None, horizontal=True)

    # NARRATIVE CONTEXT & SUBMISSION
    st.divider()
    st.subheader(t["part3_title"])
    st.markdown(t["part3_desc"])

    tab_text, tab_audio = st.tabs([t["tab_text"], t["tab_audio"]])
    
    # Math Failsafe: Only average the questions they actually answered!
    t_scores = [t1, t2, t3, t4, t5, t6, (6 - t7_raw) if t7_raw is not None else None]
    t_answered = [score for score in t_scores if score is not None]
    threat_avg = sum(t_answered) / len(t_answered) if len(t_answered) > 0 else 3.0

    d_scores = [d1, d2, d3, d4, d5, d6, (6 - d7_raw) if d7_raw is not None else None]
    d_answered = [score for score in d_scores if score is not None]
    dep_avg = sum(d_answered) / len(d_answered) if len(d_answered) > 0 else 3.0
    
    ai_reply = t["decompression_prompt"]
    next_step = "decompression"

    with tab_text:
        user_text = st.text_area("...", label_visibility="hidden", key="dmap_narrative_text")
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button(t["btn_submit_text"], type="primary", use_container_width=True):
                st.session_state.responses["threat_score_avg"] = threat_avg
                st.session_state.responses["deprivation_score_avg"] = dep_avg
                advance_chat(user_text if user_text.strip() else "[No Narrative Provided]", "text", "dmap_narrative", next_step, ai_reply)
        with col2:
            if st.button(t["btn_skip"], use_container_width=True):
                st.session_state.responses["threat_score_avg"] = threat_avg
                st.session_state.responses["deprivation_score_avg"] = dep_avg
                advance_chat("[Skipped]", "text", "dmap_narrative", next_step, ai_reply)
                
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
    with st.spinner(t["processing_audio"]):
        success = export_data_to_google()
        save_data_to_json() 
        
    if success:
        st.success(t["success"])
        
        st.divider()
        st.subheader("Your NeuroTwin Topology")
        
        t_score = st.session_state.responses.get("threat_score_avg", 3.0)
        d_score = st.session_state.responses.get("deprivation_score_avg", 3.0)
        
        st.write(f"**Calculated Threat Index:** {t_score:.2f} / 5.0")
        st.write(f"**Calculated Deprivation Index:** {d_score:.2f} / 5.0")
        
        fig = generate_neurotwin_chart(t_score, d_score)
        st.pyplot(fig)
        
    else:
        st.error("⚠️ There was a network issue. A local backup has been safely stored.")
