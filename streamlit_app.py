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
GOOGLE_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxqdvDAVoXokgjDkHbPLdGzEIdRQ0pGSgbsPukmmD-Rcc8nicwH0KsoRZ8c2P2PdavN/exec"

# TOGGLE THIS TO FALSE TO HIDE THE RADAR MAP AND EXPLANATIONS AT THE END
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
STATUS_FILE = "app_status.json"

def get_app_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, 'r') as f:
            return json.load(f).get("is_open", True)
    return True

def set_app_status(is_open):
    with open(STATUS_FILE, 'w') as f:
        json.dump({"is_open": is_open}, f)

def save_data_to_json():
    file_path = 'clinical_responses.json'
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            db = json.load(f)
    else:
        db = []
    
    # Check if participant already exists in JSON; if so, replace/update them, else append
    existing_idx = next((i for i, item in enumerate(db) if item["id"] == st.session_state.responses['id']), None)
    if existing_idx is not None:
        db[existing_idx] = st.session_state.responses
    else:
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

def process_early_exit(status_message):
    """Saves whatever partial data has been collected before closing the app."""
    st.session_state.responses["post_gate_status"] = status_message
    with st.spinner("Saving partial progress..."):
        export_data_to_google()
        save_data_to_json()
    st.session_state.current_step = 'safe_exit'
    st.rerun()

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

# ==========================================
# FULL LANGUAGE DICTIONARY
# ==========================================
CONTENT = {
    "English": {
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
        "safe_exit_msg": "Your well-being is our priority. Your partial responses have been saved. \n\n*Note: To protect your privacy, if you wish to complete the assessment later, your progress will restart from the beginning.*",
        "break_msg": "Take all the time you need. Leave this window open, and click below when you are ready to resume.",
        "btn_resume": "I am ready to resume",
        "skip_note": "💙 *Gentle reminder: You may skip any question and leave it blank if you prefer not to answer.*",
        "audio_hint": "🎙️ **Audio:** Click the microphone to start, and click again to stop (auto-stops after 5 mins). *Note: Audio files may take a few moments to upload when you click Continue.*",
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
    },
    "Mandarin": {
        "gate1_q": "您目前是否处于一个安全、私密且舒适的环境中来反思个人话题？",
        "gate1_yes": "是的，我在安全的空间",
        "gate1_no": "不在，我需要退出",
        "gate2_q": "本问卷涉及童年经历，有些可能难以回首。您可以跳过任何问题或随时停止。您希望继续吗？",
        "gate2_yes": "是的，我希望继续",
        "gate2_no": "不，我想停止",
        "mid_gate_q": "您已完成第一部分。在继续之前，您现在感觉如何？",
        "mid_gate_continue": "我感觉很好，可以继续",
        "mid_gate_break": "我想休息一下",
        "mid_gate_stop": "我想在此停止",
        "post_gate_q": "感谢您的完成。反思过去的经历可能会引发情绪波动。您现在感觉如何？",
        "post_gate_fine": "我感觉很好",
        "post_gate_unsettled": "我感觉有些不安，但还可以",
        "post_gate_talk": "我想找人谈谈",
        "crisis_msg": "如果您需要紧急支持，请联系以下服务机构：",
        "crisis_resources": "- **危机热线:** 请拨打当地紧急心理援助热线",
        "safe_exit_msg": "您的健康是我们的首要任务。您的部分回复已保存。\n\n*注意：为保护隐私，如果您希望以后完成评估，进度将重新开始。*",
        "break_msg": "请慢慢来。保留此窗口打开，准备好后点击下方按钮继续。",
        "btn_resume": "我准备好继续了",
        "skip_note": "💙 *温馨提示：如果您不想回答某些问题，可以随时跳过并留空。*",
        "audio_hint": "🎙️ **录音:** 点击麦克风开始录音，再次点击停止（5分钟后自动停止）。*注意：点击继续后，音频文件可能需要一些时间上传。*",
        "scale_desc": "**评分表:** `1=从不` | `2=很少` | `3=有时` | `4=经常` | `5=总是`",
        "btn_continue": "继续",
        "part1_title": "第一部分：威胁指标",
        "t1": "T1: 在自己家里，我感到需要时刻保持警惕或如履薄冰。",
        "t2": "T2: 生活中的成年人使用强烈的愤怒、恐惧或恐吓来控制我的行为。",
        "t3": "T3: 我目睹了家庭成员之间激烈的身体或言语冲突。",
        "t4": "T4: 我的环境感觉不可预测；我永远不知道照顾我的人会是什么心情。",
        "t5": "T5: 我遭受过感觉过度、不安全或不可预测的身体惩罚。",
        "t6": "T6: 我依赖的人让我感到身体或情感上不安全。",
        "t7": "T7 (反向评分): 当我犯错时，我相信自己会得到温和的纠正，而不是严厉的惩罚。",
        "t_narrative_1": "在您的童年时期，您是否经历过在身体或情感上受到威胁的情况？请简要描述这些事件的性质。",
        "t_narrative_2": "这些具体的经历如何影响了您今天信任他人的能力？",
        "part2_title": "第二部分：匮乏指标",
        "d1": "D1: 我很长一段时间没有成年人询问我的想法、感受或兴趣。",
        "d2": "D2: 我家里缺乏吸引人的东西，比如要读的书、玩具或爱好。",
        "d3": "D3: 我经常不得不担心我们的基本需求（如食物、电或住房）是否能得到满足。",
        "d4": "D4: 我经常被单独留下或无人看管，时间超过了我这个年龄应有的限度。",
        "d5": "D5: 生活中的成年人很少给予赞扬、鼓励或喜爱。",
        "d6": "D6: 我没有一个成年人能可靠地帮助我做功课或教我新技能。",
        "d7": "D7 (反向评分): 我的家庭环境让人感到精神上的刺激，充满了学习的机会。",
        "d_narrative_1": "在您的童年时期，是否有那么一段时间您觉得基本的身体或情感需求一直没有得到满足？",
        "d_narrative_2": "这种支持或资源的缺失如何影响了您现在与他人的联系方式？",
        "part3_title": "第三部分：战争与冲突暴露",
        "w1": "W1: 我成长的地区周围发生过武装冲突、爆炸或军事行动。",
        "w2": "W2: 因为暴力或冲突，我被迫离开我的家园或社区。",
        "w3": "W3: 我目睹了人们因冲突或有组织的暴力而受重伤或被杀。",
        "w4": "W4: 我失去了家人或亲近的人，原因归咎于战争或政治暴力。",
        "w5": "W5: 我生活在一种必须不断分辨谁值得信任、谁可能有危险的环境中。",
        "w6": "W6: 我的社区或街区被冲突或有组织的暴力摧毁或严重破坏。",
        "w7": "W7 (反向评分): 即使在困难时期，我的社区依然保持稳定，我感到一种集体的安全感。",
        "part4_title": "第四部分：社区与文化背景",
        "c1": "C1: 当我的生活出现问题时，我做的第一件事就是向周围的人求助。",
        "c2": "C2: 我首先把自己看作群体的一部分，其次才是一个个体。",
        "c3": "C3: 影响我的家庭或社区的决定应该共同做出，而不是由一个人单独决定。",
        "c4": "C4: 我认为我的个人身份与我所属的群体紧密相连。",
        "c5": "C5: 当我取得成功时，我觉得这是因为周围人的支持，而不仅仅是我自己的努力。",
        "c6": "C6: 如果必须在个人成就和群体的福祉之间做出选择，我会选择我的群体。",
        "part5_title": "第五部分：叙事背景",
        "final_q1": "如果您能改变关于您童年的一件事，那会是什么？",
        "final_q2": "用一个词来形容，那段经历如何塑造了今天的您？",
        "final_q3": "用一句话概括，当您感到不安全时，您会怎么做？"
    },
    "Cantonese": {
        "gate1_q": "你而家係咪喺一個安全、私密同舒適嘅環境入面進行反思？",
        "gate1_yes": "係，我喺安全嘅空間",
        "gate1_no": "唔係，我需要退出",
        "gate2_q": "呢份問卷會問到童年經歷，有啲可能好難回想。你可以跳過任何問題或者隨時停低。你想繼續嗎？",
        "gate2_yes": "係，我想繼續",
        "gate2_no": "唔想，我想停",
        "mid_gate_q": "你已經完成咗第一部分。喺繼續之前，你而家覺得點？",
        "mid_gate_continue": "我OK，可以繼續",
        "mid_gate_break": "我想休息吓",
        "mid_gate_stop": "我想喺度停",
        "post_gate_q": "多謝你完成問卷。回想過去可能會引起情緒波動。你而家覺得點？",
        "post_gate_fine": "我冇嘢，幾好",
        "post_gate_unsettled": "有少少唔安樂，但都OK",
        "post_gate_talk": "我想搵人傾吓",
        "crisis_msg": "如果你需要緊急支援，請聯絡以下機構：",
        "crisis_resources": "- **危機熱線:** 請致電當地緊急心理輔導熱線",
        "safe_exit_msg": "你嘅健康係我哋嘅首要考慮。你嘅部分回覆已經儲存。\n\n*注意：為咗保護私隱，如果你想遲啲完成評估，進度會重新開始。*",
        "break_msg": "慢慢嚟。保留呢個視窗打開，準備好之後㩒下面個掣繼續。",
        "btn_resume": "我準備好繼續喇",
        "skip_note": "💙 *溫馨提示：如果你唔想答某啲問題，可以隨時跳過留空。*",
        "audio_hint": "🎙️ **錄音:** 㩒咪高峰開始錄音，再㩒一次停止（5分鐘後會自動停）。*注意：㩒繼續之後，音頻文件可能需要啲時間上傳。*",
        "scale_desc": "**評分表:** `1=從來唔係` | `2=好少` | `3=有時` | `4=經常` | `5=一直都係`",
        "btn_continue": "繼續",
        "part1_title": "第一部分：威脅指標",
        "t1": "T1: 喺自己屋企，我會覺得需要時刻保持警惕或者步步為營。",
        "t2": "T2: 生活中嘅成年人會用強烈嘅憤怒、恐懼或者恐嚇嚟控制我。",
        "t3": "T3: 我見過屋企人之間有激烈嘅身體或者言語衝突。",
        "t4": "T4: 我嘅環境感覺好難預測；我永遠唔知照顧我嘅人會有咩心情。",
        "t5": "T5: 我受過覺得過度、唔安全或者難以預料嘅體罰。",
        "t6": "T6: 我依賴嘅人令我喺身體或者情感上覺得唔安全。",
        "t7": "T7 (反向評分): 當我做錯事，我信自己會得到溫和嘅教導，而唔係嚴厲嘅懲罰。",
        "t_narrative_1": "喺你嘅童年，你有冇試過喺身體或者情感上受到威脅？請簡單形容吓呢啲事。",
        "t_narrative_2": "呢啲具體嘅經歷點樣影響你今日信任其他人嘅能力？",
        "part2_title": "第二部分：匱乏指標",
        "d1": "D1: 我好長一段時間冇成年人問過我嘅想法、感受或者興趣。",
        "d2": "D2: 我屋企冇吸引人嘅嘢做，好似睇書、玩玩具或者培養愛好。",
        "d3": "D3: 我成日要擔心我哋嘅基本需求（例如夠唔夠食物、水電或者穩定住處）得唔得到滿足。",
        "d4": "D4: 我成日俾人單獨留低或者無人睇管，時間超過咗我呢個年紀應有嘅限度。",
        "d5": "D5: 生活中嘅成年人好少會讚我、鼓勵我或者錫我。",
        "d6": "D6: 我冇一個成年人可以可靠咁幫我做功課或者教我新嘢。",
        "d7": "D7 (反向評分): 我嘅家庭環境令人覺得有精神上嘅刺激，充滿學習機會。",
        "d_narrative_1": "喺你嘅童年，有冇試過覺得自己基本嘅身體或者情感需求一直得唔到滿足？",
        "d_narrative_2": "呢種缺乏支援或者資源嘅情況點樣影響你而家同其他人嘅關係？",
        "part3_title": "第三部分：戰爭與衝突暴露",
        "w1": "W1: 我大嘅地方周圍有武裝衝突、爆炸或者軍事行動發生。",
        "w2": "W2: 因為暴力或者衝突，我被迫離開我嘅屋企或者社區。",
        "w3": "W3: 我見到有人因為衝突或者有組織暴力受重傷甚至死亡。",
        "w4": "W4: 我有屋企人或者親近嘅人因為戰爭或者政治暴力過身。",
        "w5": "W5: 我生活喺一個要不斷去分辨邊個信得過、邊個有危險嘅環境。",
        "w6": "W6: 我嘅社區或者街坊俾衝突或者有組織暴力破壞或者嚴重影響。",
        "w7": "W7 (反向評分): 就算喺艱難時期，我嘅社區都保持穩定，我有一種集體嘅安全感。",
        "part4_title": "第四部分：社區與文化背景",
        "c1": "C1: 當我生活出問題嗰陣，我第一時間會去搵身邊嘅人幫手。",
        "c2": "C2: 我首先當自己係群體嘅一部分，然後先係一個個體。",
        "c3": "C3: 影響我屋企或者社區嘅決定應該一齊做，而唔係由一個人話事。",
        "c4": "C4: 我覺得我嘅個人身份同我屬於嘅群體係息息相關嘅。",
        "c5": "C5: 當我成功嗰陣，我覺得係因為身邊人嘅支持，而唔單止係自己嘅努力。",
        "c6": "C6: 如果要喺個人成就同群體福祉之間揀，我會揀我嘅群體。",
        "part5_title": "第五部分：敘事背景",
        "final_q1": "如果你可以改變童年嘅一件事，你會改變啲乜？",
        "final_q2": "用一個詞語嚟講，嗰段經歷點樣塑造咗今日嘅你？",
        "final_q3": "用一句話嚟講，當你覺得唔安全嗰陣，你會做啲乜？"
    },
    "Spanish": {
        "gate1_q": "¿Se encuentra actualmente en un entorno seguro, privado y cómodo para reflexionar sobre temas personales?",
        "gate1_yes": "Sí, estoy en un espacio seguro",
        "gate1_no": "No, necesito salir",
        "gate2_q": "Este cuestionario trata sobre experiencias de la infancia que pueden ser difíciles de recordar. Puede omitir cualquier pregunta o detenerse en cualquier momento. ¿Desea continuar?",
        "gate2_yes": "Sí, deseo continuar",
        "gate2_no": "No, me gustaría parar",
        "mid_gate_q": "Ha completado la primera parte. Antes de continuar, ¿cómo se siente en este momento?",
        "mid_gate_continue": "Me siento cómodo/a para continuar",
        "mid_gate_break": "Me gustaría tomar un descanso",
        "mid_gate_stop": "Me gustaría parar aquí",
        "post_gate_q": "Gracias por completar esto. Reflexionar sobre el pasado puede despertar emociones. ¿Cómo se siente ahora?",
        "post_gate_fine": "Me siento bien",
        "post_gate_unsettled": "Me siento un poco inquieto/a, pero bien",
        "post_gate_talk": "Me gustaría hablar con alguien",
        "crisis_msg": "Si necesita apoyo inmediato, comuníquese con uno de los siguientes servicios:",
        "crisis_resources": "- **Línea de Crisis Nacional:** Marque 988 (EE. UU.)",
        "safe_exit_msg": "Su bienestar es nuestra prioridad. Sus respuestas parciales han sido guardadas.\n\n*Nota: Para proteger su privacidad, si desea completar la evaluación más tarde, su progreso se reiniciará.*",
        "break_msg": "Tómese el tiempo que necesite. Deje esta ventana abierta y haga clic abajo cuando esté listo/a.",
        "btn_resume": "Estoy listo/a para continuar",
        "skip_note": "💙 *Recordatorio: Puede omitir cualquier pregunta y dejarla en blanco si lo prefiere.*",
        "audio_hint": "🎙️ **Audio:** Haga clic en el micrófono para comenzar y vuelva a hacer clic para detener (se detiene automáticamente después de 5 min). *Nota: Los archivos de audio pueden tardar unos momentos en cargarse al hacer clic en Continuar.*",
        "scale_desc": "**Escala:** `1=Nunca` | `2=Raramente` | `3=A veces` | `4=A menudo` | `5=Muy a menudo`",
        "btn_continue": "Continuar",
        "part1_title": "Parte 1: Indicadores de Amenaza",
        "t1": "T1: Sentía la necesidad constante de estar en guardia en mi propia casa.",
        "t2": "T2: Los adultos usaban ira intensa, miedo o intimidación para controlarme.",
        "t3": "T3: Fui testigo de conflictos físicos o verbales agresivos en mi hogar.",
        "t4": "T4: Mi entorno era impredecible; nunca sabía de qué humor estarían mis cuidadores.",
        "t5": "T5: Fui sometido/a a disciplina física que sentí excesiva o insegura.",
        "t6": "T6: Las personas de las que dependía me hacían sentir inseguro/a.",
        "t7": "T7 (Inverso): Cuando cometía un error, confiaba en que me corregirían con suavidad.",
        "t_narrative_1": "¿Experimentó situaciones en las que se sintió amenazado/a física o emocionalmente durante su infancia? Describa brevemente.",
        "t_narrative_2": "¿Cómo influyeron esas experiencias en su capacidad para confiar en los demás hoy en día?",
        "part2_title": "Parte 2: Indicadores de Privación",
        "d1": "D1: Pasaba largos períodos sin que los adultos preguntaran sobre mis sentimientos o intereses.",
        "d2": "D2: A mi hogar le faltaban cosas interesantes para hacer o pasatiempos.",
        "d3": "D3: A menudo tenía que preocuparme de si se cubrirían nuestras necesidades básicas.",
        "d4": "D4: Con frecuencia me dejaban solo/a o sin supervisión demasiado tiempo.",
        "d5": "D5: Era raro que los adultos me ofrecieran elogios o afecto.",
        "d6": "D6: No tenía un adulto que me ayudara de manera confiable con la escuela.",
        "d7": "D7 (Inverso): Mi entorno familiar se sentía mentalmente estimulante.",
        "d_narrative_1": "¿Hubo momentos en su infancia en los que sintió que sus necesidades básicas no fueron satisfechas?",
        "d_narrative_2": "¿Cómo ha influido esta ausencia de apoyo en la forma en que se conecta con los demás ahora?",
        "part3_title": "Parte 3: Exposición a la Guerra y el Conflicto",
        "w1": "W1: Crecí en un área donde ocurrían conflictos armados, bombardeos u operaciones militares.",
        "w2": "W2: Me vi obligado/a a dejar mi hogar debido a la violencia o el conflicto.",
        "w3": "W3: Fui testigo de personas gravemente heridas o asesinadas como resultado de violencia organizada.",
        "w4": "W4: Perdí a un familiar o alguien cercano debido a la guerra o violencia política.",
        "w5": "W5: Viví en un entorno en el que tenía que averiguar constantemente en quién confiar.",
        "w6": "W6: Mi comunidad fue destruida o gravemente perturbada por la violencia.",
        "w7": "W7 (Inverso): Incluso en tiempos difíciles, mi comunidad se mantuvo estable y me sentí seguro/a.",
        "part4_title": "Parte 4: Contexto Cultural y Comunitario",
        "c1": "C1: Cuando algo sale mal en mi vida, lo primero que hago es acudir a las personas que me rodean.",
        "c2": "C2: Me veo a mí mismo/a primero como parte de un grupo, y luego como individuo.",
        "c3": "C3: Las decisiones que afectan a mi familia o comunidad deben tomarse juntos, no por una sola persona.",
        "c4": "C4: Describiría mi identidad personal como estrechamente ligada a los grupos a los que pertenezco.",
        "c5": "C5: Cuando tengo éxito, siento que es por el apoyo de quienes me rodean, no solo por mi propio esfuerzo.",
        "c6": "C6: Si tuviera que elegir entre el logro personal y el bienestar de mi grupo, elegiría a mi grupo.",
        "part5_title": "Parte 5: Contexto Narrativo",
        "final_q1": "Si pudiera cambiar una cosa de su infancia, ¿cuál sería?",
        "final_q2": "En una palabra, ¿cómo moldeó esa experiencia quién es usted hoy?",
        "final_q3": "En una oración, ¿qué hace cuando se siente inseguro/a?"
    },
    "French": {
        "gate1_q": "Êtes-vous actuellement dans un environnement sûr, privé et confortable pour réfléchir à des sujets personnels ?",
        "gate1_yes": "Oui, je suis dans un espace sûr",
        "gate1_no": "Non, je dois quitter",
        "gate2_q": "Ce questionnaire porte sur des expériences d'enfance, dont certaines peuvent être difficiles. Vous pouvez passer des questions ou arrêter. Souhaitez-vous continuer ?",
        "gate2_yes": "Oui, je souhaite continuer",
        "gate2_no": "Non, je voudrais arrêter",
        "mid_gate_q": "Vous avez terminé la première partie. Comment vous sentez-vous en ce moment ?",
        "mid_gate_continue": "Je suis à l'aise pour continuer",
        "mid_gate_break": "J'aimerais faire une pause",
        "mid_gate_stop": "J'aimerais m'arrêter ici",
        "post_gate_q": "Merci d'avoir terminé. Réfléchir au passé peut susciter des émotions. Comment vous sentez-vous ?",
        "post_gate_fine": "Je me sens bien",
        "post_gate_unsettled": "Je me sens un peu perturbé(e) mais ça va",
        "post_gate_talk": "J'aimerais parler à quelqu'un",
        "crisis_msg": "Si vous avez besoin d'un soutien immédiat, veuillez contacter :",
        "crisis_resources": "- **Ligne d'assistance de crise :** Numéro d'urgence local",
        "safe_exit_msg": "Votre bien-être est notre priorité. Vos réponses partielles ont été enregistrées.\n\n*Remarque : Pour protéger votre vie privée, si vous souhaitez terminer l'évaluation plus tard, votre progression recommencera.*",
        "break_msg": "Prenez votre temps. Laissez cette fenêtre ouverte et cliquez ci-dessous lorsque vous êtes prêt(e).",
        "btn_resume": "Je suis prêt(e) à reprendre",
        "skip_note": "💙 *Rappel : Vous pouvez ignorer toute question et la laisser vide si vous préférez.*",
        "audio_hint": "🎙️ **Audio:** Cliquez sur le microphone pour commencer, et cliquez à nouveau pour arrêter (arrêt automatique après 5 min). *Remarque : Le téléchargement des fichiers audio peut prendre quelques instants après avoir cliqué sur Continuer.*",
        "scale_desc": "**Échelle:** `1=Jamais` | `2=Rarement` | `3=Parfois` | `4=Souvent` | `5=Très souvent`",
        "btn_continue": "Continuer",
        "part1_title": "Partie 1 : Indicateurs de Menace",
        "t1": "T1: Je ressentais un besoin constant d'être sur mes gardes dans ma propre maison.",
        "t2": "T2: Les adultes utilisaient une colère intense ou l'intimidation pour me contrôler.",
        "t3": "T3: J'ai été témoin de conflits physiques ou verbaux agressifs dans mon foyer.",
        "t4": "T4: Mon environnement me semblait imprévisible ; je ne savais jamais de quelle humeur seraient les adultes.",
        "t5": "T5: J'ai subi une discipline physique excessive ou dangereuse.",
        "t6": "T6: Les personnes dont je dépendais me faisaient me sentir en insécurité.",
        "t7": "T7 (Inversé): Quand je faisais une erreur, je savais que je serais corrigé(e) doucement.",
        "t_narrative_1": "Avez-vous vécu des moments où vous vous êtes senti(e) menacé(e) physiquement ou émotionnellement pendant votre enfance ?",
        "t_narrative_2": "Comment ces expériences influencent-elles votre capacité à faire confiance aux autres aujourd'hui ?",
        "part2_title": "Partie 2 : Indicateurs de Privation",
        "d1": "D1: Je passais de longues périodes sans que les adultes ne s'intéressent à mes pensées.",
        "d2": "D2: Ma maison manquait de choses stimulantes à faire.",
        "d3": "D3: Je devais souvent m'inquiéter de savoir si nos besoins fondamentaux seraient satisfaits.",
        "d4": "D4: J'étais fréquemment laissé(e) seul(e) trop longtemps pour mon âge.",
        "d5": "D5: Il était rare que les adultes m'offrent des éloges ou de l'affection.",
        "d6": "D6: Je n'avais pas d'adulte pour m'aider de manière fiable avec l'école.",
        "d7": "D7 (Inversé): Mon environnement familial me semblait mentalement stimulant.",
        "d_narrative_1": "Y a-t-il eu des moments où vous avez senti que vos besoins fondamentaux n'étaient pas satisfaits ?",
        "d_narrative_2": "Comment cette absence de soutien influence-t-elle votre façon de créer des liens avec les autres ?",
        "part3_title": "Partie 3 : Exposition à la Guerre et aux Conflits",
        "w1": "W1: J'ai grandi dans une région où des conflits armés ou des bombardements se produisaient autour de moi.",
        "w2": "W2: J'ai été forcé(e) de quitter ma maison à cause de la violence.",
        "w3": "W3: J'ai vu des personnes être gravement blessées ou tuées à cause de conflits.",
        "w4": "W4: J'ai perdu un membre de ma famille à cause de la guerre ou de la violence politique.",
        "w5": "W5: J'ai vécu dans un environnement où je devais constamment deviner à qui faire confiance.",
        "w6": "W6: Ma communauté a été détruite ou gravement perturbée par la violence.",
        "w7": "W7 (Inversé): Même dans les moments difficiles, ma communauté est restée stable.",
        "part4_title": "Partie 4 : Contexte Communautaire et Culturel",
        "c1": "C1: Quand quelque chose va mal dans ma vie, la première chose que je fais est de me tourner vers mon entourage.",
        "c2": "C2: Je me considère d'abord comme faisant partie d'un groupe, puis comme un individu.",
        "c3": "C3: Les décisions qui affectent ma famille ou ma communauté doivent être prises ensemble.",
        "c4": "C4: Je décrirais mon identité personnelle comme étroitement liée aux groupes auxquels j'appartiens.",
        "c5": "C5: Quand je réussis, je sens que c'est grâce au soutien de ceux qui m'entourent.",
        "c6": "C6: Si je devais choisir entre la réussite personnelle et le bien-être de mon groupe, je choisirais mon groupe.",
        "part5_title": "Partie 5 : Contexte Narratif",
        "final_q1": "Si vous pouviez changer une chose de votre enfance, quelle serait-elle ?",
        "final_q2": "En un mot, comment cette expérience a-t-elle façonné qui vous êtes aujourd'hui ?",
        "final_q3": "En une phrase, que faites-vous lorsque vous vous sentez en insécurité ?"
    },
    "Russian": {
        "gate1_q": "Находитесь ли вы сейчас в безопасной, уединенной и комфортной обстановке?",
        "gate1_yes": "Да, я в безопасности",
        "gate1_no": "Нет, мне нужно выйти",
        "gate2_q": "Этот опросник касается детских переживаний. Вы можете пропустить любой вопрос. Вы хотите продолжить?",
        "gate2_yes": "Да, я хочу продолжить",
        "gate2_no": "Нет, я хотел(а) бы остановиться",
        "mid_gate_q": "Вы завершили первую часть. Как вы себя чувствуете сейчас?",
        "mid_gate_continue": "Мне комфортно продолжать",
        "mid_gate_break": "Я хотел(а) бы сделать перерыв",
        "mid_gate_stop": "Я хотел(а) бы остановиться",
        "post_gate_q": "Спасибо за ответы. Воспоминания о прошлом могут вызывать эмоции. Как вы себя чувствуете?",
        "post_gate_fine": "Я чувствую себя хорошо",
        "post_gate_unsettled": "Немного не по себе, но в целом нормально",
        "post_gate_talk": "Я хотел(а) бы поговорить с кем-нибудь",
        "crisis_msg": "Если вам нужна срочная поддержка, обратитесь в одну из служб:",
        "crisis_resources": "- **Телефон доверия:** Обратитесь в местную службу поддержки",
        "safe_exit_msg": "Мы безопасно закрыли вашу сессию. Ваши частичные ответы сохранены.\n\n*Примечание: В целях вашей безопасности, если вы захотите завершить оценку позже, ваш прогресс будет сброшен.*",
        "break_msg": "Не торопитесь. Оставьте окно открытым и нажмите ниже, когда будете готовы.",
        "btn_resume": "Я готов(а) продолжить",
        "skip_note": "💙 *Напоминание: Вы можете пропустить любой вопрос и оставить его пустым.*",
        "audio_hint": "🎙️ **Аудио:** Нажмите на микрофон, чтобы начать, и еще раз, чтобы остановить (автоматически остановится через 5 мин). *Примечание: Загрузка аудиофайлов может занять некоторое время при нажатии кнопки 'Продолжить'.*",
        "scale_desc": "**Шкала:** `1=Никогда` | `2=Редко` | `3=Иногда` | `4=Часто` | `5=Очень часто`",
        "btn_continue": "Продолжить",
        "part1_title": "Часть 1: Индикаторы Угрозы",
        "t1": "T1: Я чувствовал(а) постоянную необходимость быть начеку в собственном доме.",
        "t2": "T2: Взрослые использовали сильный гнев, страх или запугивание, чтобы контролировать меня.",
        "t3": "T3: Я был(а) свидетелем агрессивных конфликтов в семье.",
        "t4": "T4: Моя среда казалась непредсказуемой.",
        "t5": "T5: Я подвергался(-ась) чрезмерным физическим наказаниям.",
        "t6": "T6: Люди, от которых я зависел(а), заставляли меня чувствовать себя небезопасно.",
        "t7": "T7 (Обратная): Когда я совершал(а) ошибку, меня поправляли мягко.",
        "t_narrative_1": "Были ли в вашем детстве случаи, когда вы чувствовали физическую или эмоциональную угрозу?",
        "t_narrative_2": "Как этот опыт влияет на вашу способность доверять другим сегодня?",
        "part2_title": "Часть 2: Индикаторы Лишений",
        "d1": "D1: Взрослые подолгу не спрашивали о моих мыслях или чувствах.",
        "d2": "D2: В моем доме не было интересных занятий или игрушек.",
        "d3": "D3: Мне часто приходилось беспокоиться о базовых потребностях.",
        "d4": "D4: Меня часто оставляли одного/одну без присмотра.",
        "d5": "D5: Взрослые редко хвалили или поощряли меня.",
        "d6": "D6: У меня не было взрослого, который бы надежно помогал мне с уроками.",
        "d7": "D7 (Обратная): В детстве у меня было много возможностей для обучения и развития.",
        "d_narrative_1": "Были ли в вашем детстве периоды, когда ваши базовые потребности не удовлетворялись?",
        "d_narrative_2": "Как это отсутствие поддержки влияет на то, как вы общаетесь с другими сейчас?",
        "part3_title": "Часть 3: Война и Конфликты",
        "w1": "W1: Я вырос(ла) в районе, где происходили вооруженные конфликты или бомбежки.",
        "w2": "W2: Я был(а) вынужден(а) покинуть свой дом из-за насилия.",
        "w3": "W3: Я был(а) свидетелем того, как люди получали серьезные травмы из-за конфликтов.",
        "w4": "W4: Я потерял(а) члена семьи на войне или из-за политического насилия.",
        "w5": "W5: Я жил(а) в среде, где приходилось постоянно думать, кому можно доверять.",
        "w6": "W6: Мой район был разрушен из-за конфликта.",
        "w7": "W7 (Обратная): Даже в трудные времена моя община оставалась стабильной, и я чувствовал(а) безопасность.",
        "part4_title": "Часть 4: Культурный Контекст",
        "c1": "C1: Когда в моей жизни что-то идет не так, я первым делом обращаюсь к окружающим.",
        "c2": "C2: Я вижу себя в первую очередь частью группы, а затем индивидом.",
        "c3": "C3: Решения, затрагивающие мою семью или общину, должны приниматься сообща.",
        "c4": "C4: Я бы описал(а) свою личность как тесно связанную с группами, к которым я принадлежу.",
        "c5": "C5: Когда я добиваюсь успеха, я чувствую, что это заслуга поддержки окружающих.",
        "c6": "C6: Если бы мне пришлось выбирать между личных достижениях и благополучием группы, я бы выбрал(а) группу.",
        "part5_title": "Часть 5: Нарративный Контекст",
        "final_q1": "Если бы вы могли изменить одну вещь в своем детстве, что бы это было?",
        "final_q2": "Одним словом, как этот опыт сформировал вас сегодняшнего?",
        "final_q3": "Одним предложением, что вы делаете, когда чувствуете себя в опасности?"
    },
    "Turkish": {
        "gate1_q": "Şu anda kişisel konular üzerine düşünmek için güvenli, özel ve rahat bir ortamda mısınız?",
        "gate1_yes": "Evet, güvenli bir alandayım",
        "gate1_no": "Hayır, çıkmam gerekiyor",
        "gate2_q": "Bu anket çocukluk deneyimlerinizi sormaktadır; bazılarını hatırlamak zor olabilir. İstediğiniz soruyu atlayabilir veya durabilirsiniz. Devam etmek istiyor musunuz?",
        "gate2_yes": "Evet, devam etmek istiyorum",
        "gate2_no": "Hayır, durmak istiyorum",
        "mid_gate_q": "İlk bölümü tamamladınız. Devam etmeden önce, şu an nasıl hissediyorsunuz?",
        "mid_gate_continue": "Devam etmeye hazırım",
        "mid_gate_break": "Biraz ara vermek istiyorum",
        "mid_gate_stop": "Burada durmak istiyorum",
        "post_gate_q": "Tamamladığınız için teşekkürler. Geçmiş deneyimleri düşünmek duyguları tetikleyebilir. Şu an nasıl hissediyorsunuz?",
        "post_gate_fine": "İyi hissediyorum",
        "post_gate_unsettled": "Biraz huzursuz hissediyorum ama iyiyim",
        "post_gate_talk": "Biriyle konuşmak istiyorum",
        "crisis_msg": "Acil desteğe ihtiyacınız varsa, lütfen aşağıdaki hizmetlerden biriyle iletişime geçin:",
        "crisis_resources": "- **Kriz Hattı:** Lütfen yerel acil numarayı arayın",
        "safe_exit_msg": "Güvenliğiniz bizim önceliğimizdir. Kısmi yanıtlarınız kaydedildi.\n\n*Not: Gizliliğinizi korumak için, anketi daha sonra tamamlamak isterseniz ilerlemeniz yeniden başlayacaktır.*",
        "break_msg": "İstediğiniz kadar zaman ayırın. Hazır olduğunuzda devam etmek için aşağıya tıklayın.",
        "btn_resume": "Devam etmeye hazırım",
        "skip_note": "💙 *Hatırlatma: Cevaplamak istemediğiniz soruları boş bırakabilirsiniz.*",
        "audio_hint": "🎙️ **Ses:** Başlamak için mikrofona tıklayın, durdurmak için tekrar tıklayın (5 dk sonra otomatik durur). *Not: Devam'a tıkladığınızda ses dosyalarının yüklenmesi biraz zaman alabilir.*",
        "scale_desc": "**Ölçek:** `1=Hiçbir zaman` | `2=Nadiren` | `3=Bazen` | `4=Sıklıkla` | `5=Her zaman`",
        "btn_continue": "Devam et",
        "part1_title": "Bölüm 1: Tehdit Göstergeleri",
        "t1": "T1: Kendi evimde sürekli tetikte olma veya 'yumurta kabukları üzerinde yürüme' ihtiyacı hissettim.",
        "t2": "T2: Hayatımdaki yetişkinler davranışlarımı kontrol etmek için öfke, korku veya sindirme kullandı.",
        "t3": "T3: Evimde insanlar arasında agresif fiziksel veya sözlü çatışmalara tanık oldum.",
        "t4": "T4: Çevrem öngörülemezdi; bakıcılarımın ne ruh halinde olacağını asla bilemezdim.",
        "t5": "T5: Aşırı veya güvensiz hissettiren fiziksel disipline maruz kaldım.",
        "t6": "T6: Güvendiğim insanlar beni fiziksel veya duygusal olarak güvende hissettirmedi.",
        "t7": "T7 (Ters): Hata yaptığımda sertçe değil, nazikçe düzeltileceğime güveniyordum.",
        "t_narrative_1": "Çocukluğunuzda fiziksel veya duygusal olarak tehdit altında hissettiğiniz anlar oldu mu? Lütfen kısaca anlatın.",
        "t_narrative_2": "Bu deneyimler bugün başkalarına güvenme yeteneğinizi nasıl etkiliyor?",
        "part2_title": "Bölüm 2: Yoksunluk Göstergeleri",
        "d1": "D1: Uzun süre yetişkinlerin benim düşüncelerimi veya hislerimi sormadığı zamanlar oldu.",
        "d2": "D2: Evimde kitap okumak, oyuncaklar veya hobiler gibi ilgi çekici şeyler eksikti.",
        "d3": "D3: Sık sık temel ihtiyaçlarımızın karşılanıp karşılanmayacağı konusunda endişelenmek zorunda kaldım.",
        "d4": "D4: Sıklıkla yaşıma uygun olmayan uzun süreler yalnız bırakıldım.",
        "d5": "D5: Yetişkinlerin bana övgü, teşvik veya sevgi sunması nadirdi.",
        "d6": "D6: Bana okul ödevlerimde güvenilir bir şekilde yardım eden bir yetişkin yoktu.",
        "d7": "D7 (Ters): Ev ortamım zihinsel olarak uyarıcı hissettiriyordu.",
        "d_narrative_1": "Çocukluğunuzda temel fiziksel veya duygusal ihtiyaçlarınızın karşılanmadığını hissettiğiniz zamanlar oldu mu?",
        "d_narrative_2": "Bu destek eksikliği şimdi başkalarıyla kurduğunuz bağları nasıl etkiliyor?",
        "part3_title": "Bölüm 3: Savaş ve Çatışma Maruziyeti",
        "w1": "W1: Silahlı çatışmaların veya bombalamaların olduğu bir bölgede büyüdüm.",
        "w2": "W2: Şiddet nedeniyle evimi terk etmek zorunda kaldım.",
        "w3": "W3: İnsanların çatışma nedeniyle ciddi şekilde yaralandığına veya öldürüldüğüne tanık oldum.",
        "w4": "W4: Savaş veya siyasi şiddet nedeniyle bir aile üyemi kaybettim.",
        "w5": "W5: Sürekli olarak kime güvenilebileceğini anlamak zorunda olduğum bir çevrede yaşadım.",
        "w6": "W6: Mahallem çatışma nedeniyle yıkıldı veya ciddi şekilde bozuldu.",
        "w7": "W7 (Ters): Zor zamanlarda bile topluluğum sabit kaldı ve güvende hissettim.",
        "part4_title": "Bölüm 4: Kültürel Bağlam",
        "c1": "C1: Hayatımda bir şeyler ters gittiğinde ilk yaptığım şey çevremdeki insanlara ulaşmaktır.",
        "c2": "C2: Kendimi önce bir grubun parçası, sonra bir birey olarak görüyorum.",
        "c3": "C3: Ailemi etkileyen kararlar tek bir kişi tarafından değil, birlikte alınmalıdır.",
        "c4": "C4: Kişisel kimliğimi ait olduğum gruplarla yakından bağlantılı olarak tanımlarım.",
        "c5": "C5: Başarılı olduğumda, bunun sadece kendi çabam değil, çevremin desteği sayesinde olduğunu hissederim.",
        "c6": "C6: Kişisel başarı ile grubumun refahı arasında seçim yapmam gerekseydi, grubumu seçerdim.",
        "part5_title": "Bölüm 5: Anlatı Bağlamı",
        "final_q1": "Çocukluğunuz hakkında bir şeyi değiştirebilseydiniz, bu ne olurdu?",
        "final_q2": "Tek bir kelimeyle, o deneyim bugünkü sizi nasıl şekillendirdi?",
        "final_q3": "Tek bir cümleyle, kendinizi güvensiz hissettiğinizde ne yaparsınız?"
    },
    "German": {
        "gate1_q": "Befinden Sie sich an einem sicheren, privaten Ort, um über persönliche Themen nachzudenken?",
        "gate1_yes": "Ja, ich bin an einem sicheren Ort",
        "gate1_no": "Nein, ich muss abbrechen",
        "gate2_q": "Dieser Fragebogen behandelt Kindheitserfahrungen. Sie können jede Frage überspringen oder jederzeit abbrechen. Möchten Sie fortfahren?",
        "gate2_yes": "Ja, ich möchte fortfahren",
        "gate2_no": "Nein, ich möchte aufhören",
        "mid_gate_q": "Sie haben den ersten Teil abgeschlossen. Wie fühlen Sie sich jetzt, bevor wir fortfahren?",
        "mid_gate_continue": "Ich bin bereit fortzufahren",
        "mid_gate_break": "Ich möchte eine Pause machen",
        "mid_gate_stop": "Ich möchte hier aufhören",
        "post_gate_q": "Vielen Dank. Das Nachdenken über die Vergangenheit kann Emotionen wecken. Wie fühlen Sie sich jetzt?",
        "post_gate_fine": "Ich fühle mich gut",
        "post_gate_unsettled": "Ich bin etwas aufgewühlt, aber es geht mir gut",
        "post_gate_talk": "Ich möchte mit jemandem sprechen",
        "crisis_msg": "Wenn Sie sofortige Unterstützung benötigen, wenden Sie sich bitte an:",
        "crisis_resources": "- **Telefonseelsorge:** Bitte rufen Sie die lokale Notrufnummer an",
        "safe_exit_msg": "Ihr Wohlbefinden ist unsere Priorität. Ihre teilweisen Antworten wurden gespeichert.\n\n*Hinweis: Um Ihre Privatsphäre zu schützen, wird Ihr Fortschritt neu gestartet, wenn Sie die Bewertung später abschließen möchten.*",
        "break_msg": "Nehmen Sie sich die Zeit, die Sie brauchen. Klicken Sie unten, wenn Sie bereit sind.",
        "btn_resume": "Ich bin bereit fortzufahren",
        "skip_note": "💙 *Hinweis: Sie können jede Frage überspringen und leer lassen.*",
        "audio_hint": "🎙️ **Audio:** Klicken Sie auf das Mikrofon, um zu starten, und erneut, um zu stoppen (stoppt automatisch nach 5 Min). *Hinweis: Das Hochladen von Audiodateien kann einen Moment dauern.*",
        "scale_desc": "**Skala:** `1=Nie wahr` | `2=Selten wahr` | `3=Manchmal wahr` | `4=Oft wahr` | `5=Sehr oft wahr`",
        "btn_continue": "Fortfahren",
        "part1_title": "Teil 1: Indikatoren für Bedrohung",
        "t1": "T1: Ich spürte in meinem eigenen Zuhause ständig das Bedürfnis, auf der Hut zu sein.",
        "t2": "T2: Erwachsene nutzten extreme Wut, Angst oder Einschüchterung, um mich zu kontrollieren.",
        "t3": "T3: Ich wurde Zeuge von aggressiven Konflikten in meinem Haushalt.",
        "t4": "T4: Meine Umgebung fühlte sich unberechenbar an.",
        "t5": "T5: Ich wurde einer körperlichen Disziplinierung unterzogen, die sich unsicher anfühlte.",
        "t6": "T6: Menschen, von denen ich abhängig war, gaben mir das Gefühl der Unsicherheit.",
        "t7": "T7 (Umgekehrt): Wenn ich einen Fehler machte, vertraute ich darauf, sanft korrigiert zu werden.",
        "t_narrative_1": "Haben Sie Situationen erlebt, in denen Sie sich bedroht fühlten? Beschreiben Sie dies kurz.",
        "t_narrative_2": "Wie beeinflussen diese Erfahrungen Ihre Fähigkeit, heute anderen zu vertrauen?",
        "part2_title": "Teil 2: Indikatoren für Deprivation",
        "d1": "D1: Es gab lange Zeiten, in denen mich Erwachsene nicht nach meinen Gefühlen fragten.",
        "d2": "D2: In meinem Zuhause fehlte es an anregenden Dingen (Bücher, Spielzeug).",
        "d3": "D3: Ich musste mir oft Sorgen um unsere Grundbedürfnisse machen.",
        "d4": "D4: Ich wurde häufig länger allein gelassen, als es für mein Alter angemessen war.",
        "d5": "D5: Es war selten, dass Erwachsene mir Lob oder Zuneigung entgegenbrachten.",
        "d6": "D6: Ich hatte keinen Erwachsenen, der mir verlässlich bei den Schularbeiten half.",
        "d7": "D7 (Umgekehrt): Meine familiäre Umgebung fühlte sich geistig anregend an.",
        "d_narrative_1": "Gab es Zeiten, in denen Ihre Grundbedürfnisse nicht erfüllt wurden?",
        "d_narrative_2": "Wie beeinflusst diese fehlende Unterstützung heute Ihre Beziehungen?",
        "part3_title": "Teil 3: Krieg und Konflikt",
        "w1": "W1: Ich bin in einem Gebiet aufgewachsen, in dem es bewaffnete Konflikte gab.",
        "w2": "W2: Ich war gezwungen, mein Zuhause wegen Gewalt zu verlassen.",
        "w3": "W3: Ich wurde Zeuge, wie Menschen durch Konflikte schwer verletzt wurden.",
        "w4": "W4: Ich habe ein Familienmitglied durch Krieg oder politische Gewalt verloren.",
        "w5": "W5: Ich lebte in einem Umfeld, in dem ich ständig überlegen musste, wem ich vertrauen kann.",
        "w6": "W6: Meine Gemeinde wurde durch Konflikte zerstört.",
        "w7": "W7 (Umgekehrt): Selbst in schwierigen Zeiten fühlte ich ein kollektives Gefühl der Sicherheit.",
        "part4_title": "Teil 4: Kultureller Kontext",
        "c1": "C1: Wenn in meinem Leben etwas schiefgeht, wende ich mich zuerst an meine Mitmenschen.",
        "c2": "C2: Ich sehe mich in erster Linie als Teil einer Gruppe und erst in zweiter Linie als Individuum.",
        "c3": "C3: Entscheidungen für die Gemeinschaft sollten zusammen getroffen werden.",
        "c4": "C4: Meine persönliche Identität ist eng mit den Gruppen verbunden, denen ich angehöre.",
        "c5": "C5: Wenn ich Erfolg habe, spüre ich, dass dies der Unterstützung meines Umfelds zu verdanken ist.",
        "c6": "C6: Wenn ich wählen müsste, würde ich das Wohlergehen meiner Gruppe meinem Erfolg vorziehen.",
        "part5_title": "Teil 5: Narrativer Kontext",
        "final_q1": "Wenn Sie eine Sache an Ihrer Kindheit ändern könnten, welche wäre das?",
        "final_q2": "Mit einem Wort: Wie hat diese Erfahrung Sie geprägt?",
        "final_q3": "In einem Satz: Was tun Sie, wenn Sie sich unsicher fühlen?"
    }
}

# Language mapping dict to route native names to our backend keys
LANG_MAP = {
    "English": "English",
    "中文 (Mandarin)": "Mandarin",
    "粵語 (Cantonese)": "Cantonese",
    "Español (Spanish)": "Spanish",
    "Français (French)": "French",
    "Русский (Russian)": "Russian",
    "Türkçe (Turkish)": "Turkish",
    "Deutsch (German)": "German"
}

# ==========================================
# INITIALIZATION
# ==========================================
if 'responses' not in st.session_state:
    st.session_state.responses = {'id': datetime.now().strftime("%Y%m%d_%H%M%S")}
if 'current_step' not in st.session_state:
    st.session_state.current_step = 'dashboard'
    st.session_state.lang = "English"

# ==========================================
# SIDEBAR (ONLY FOR PUBLIC APP)
# ==========================================
with st.sidebar:
    st.subheader("Assessment Controls")
    if st.button("🔄 Restart Assessment", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    # HIDDEN TRICK: Only show the login if the URL ends in ?admin=true
    if st.query_params.get("admin") == "true":
        st.divider()
        if not st.session_state.get('admin_unlocked', False):
            admin_password = st.text_input("Admin Password", type="password")
            if st.button("Login"):
                if admin_password == st.secrets.get("admin_password", "1234"): 
                    st.session_state.admin_unlocked = True
                    st.rerun()
                else:
                    st.error("Incorrect Password")
        else:
            if st.button("Logout"):
                st.session_state.admin_unlocked = False
                st.rerun()

# ==========================================
# ADMIN DASHBOARD (FULL SCREEN)
# ==========================================
if st.session_state.get('admin_unlocked', False):
    st.title("Admin Dashboard")
    st.write("Welcome to the secure administrative view.")
    
    # --- Study Status Toggle ---
    st.subheader("Study Status")
    current_status = get_app_status()
    if current_status:
        st.success("🟢 The study is currently OPEN.")
        if st.button("Close Study", type="primary"):
            set_app_status(False)
            st.rerun()
    else:
        st.error("🔴 The study is currently CLOSED.")
        if st.button("Reopen Study", type="primary"):
            set_app_status(True)
            st.rerun()
            
    st.divider()
    
    # --- Local Data Backup ---
    file_path = 'clinical_responses.json'
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
        if data:
            df = pd.DataFrame(data)
            st.subheader("Participant Submissions (Local)")
            st.dataframe(df, use_container_width=True)
            
            # --- UPGRADED: Participant Detail View & Radar Map ---
            st.divider()
            st.subheader("Participant Clinical Profile")
            participant_ids = [entry.get('id') for entry in data if 'id' in entry]
            selected_detail_id = st.selectbox("Select ID to View Details:", ["-- Select ID --"] + participant_ids)
            
            if selected_detail_id != "-- Select ID --":
                participant_data = next((item for item in data if item.get("id") == selected_detail_id), None)
                if participant_data:
                    col_chart, col_details = st.columns([1, 1])
                    
                    # LEFT COLUMN: The Radar Map & Scores
                    with col_chart:
                        st.write("**NeuroTwin Topology Map**")
                        t_score = participant_data.get("threat_score_avg", 0)
                        d_score = participant_data.get("deprivation_score_avg", 0)
                        w_score = participant_data.get("war_score_avg", 0)
                        c_score = participant_data.get("col_score_avg", 3.0)
                        
                        fig = generate_neurotwin_chart(t_score, d_score, w_score, c_score)
                        st.pyplot(fig)
                        
                        st.info(f"**Scores:** Threat: {t_score:.2f} | Deprivation: {d_score:.2f} | War: {w_score:.2f} | Collectivism: {c_score:.2f}")

                    # RIGHT COLUMN: Clean Narratives & Audio Playback
                    with col_details:
                        st.write("**Narrative Responses**")
                        narratives = {
                            "Threat 1": participant_data.get("threat_narrative_1", ""),
                            "Threat 2": participant_data.get("threat_narrative_2", ""),
                            "Deprivation 1": participant_data.get("dep_narrative_1", ""),
                            "Deprivation 2": participant_data.get("dep_narrative_2", ""),
                            "Final (Change)": participant_data.get("final_narrative_1", ""),
                            "Final (One Word)": participant_data.get("final_narrative_2", ""),
                            "Final (Unsafe)": participant_data.get("final_narrative_3", "")
                        }
                        
                        # Print text responses cleanly
                        for title, text in narratives.items():
                            if text and text != "..." and text.strip():
                                st.markdown(f"**{title}:** {text}")
                        
                        st.write("---")
                        st.write("**Audio Recordings**")
                        # Find and create playback buttons for any saved audio
                        audio_keys = [k for k in participant_data.keys() if k.endswith("_audio")]
                        has_audio = False
                        for ak in audio_keys:
                            audio_path = participant_data[ak]
                            if os.path.exists(audio_path):
                                has_audio = True
                                clean_title = ak.replace("_audio", "").replace("_", " ").title()
                                st.write(f"*{clean_title}*")
                                st.audio(audio_path)
                        
                        if not has_audio:
                            st.write("No audio recorded for this participant.")
                    
                    # Keep the raw JSON hidden in a dropdown just in case you need it
                    with st.expander("View Raw Developer JSON Data"):
                        st.json(participant_data)
            
            st.divider()
            
            # --- Data Management ---
            col1, col2 = st.columns(2)
            with col1:
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(label="📥 Download Data as CSV", data=csv, file_name="dmap_local_backup.csv", mime="text/csv", use_container_width=True)
            with col2:
                selected_del_id = st.selectbox("Select ID to Delete:", ["-- Select ID --"] + participant_ids, label_visibility="collapsed")
                if st.button("🗑️ Delete Selected Participant", use_container_width=True) and selected_del_id != "-- Select ID --":
                    new_data = [entry for entry in data if entry.get('id') != selected_del_id]
                    with open(file_path, 'w') as f:
                        json.dump(new_data, f, indent=4)
                    st.success(f"Participant {selected_del_id} deleted!")
                    st.rerun()

            st.warning("⚠️ Proceed with caution. This will delete the entire local JSON backup on this server.")
            if st.button("🚨 Clear All Local Data", type="primary"):
                with open(file_path, 'w') as f:
                    json.dump([], f, indent=4)
                st.success("All local data cleared!")
                st.rerun()
        else:
            st.info("No responses recorded yet.")
    else:
        st.info("The local database file has not been created yet.")
        
    st.stop() # Prevents the rest of the public app from rendering when admin is logged in!

# ==========================================
# STUDY STATUS GATE (PUBLIC VIEW)
# ==========================================
if not get_app_status() and not st.session_state.get('admin_unlocked', False):
    st.title("NeuroTwin: Many Ways to Thrive")
    st.info("Thank you for your interest! This study is currently closed to new responses.")
    st.stop()

# ==========================================
# THE STATE MACHINE 
# ==========================================
t = CONTENT[st.session_state.lang]

if st.session_state.current_step == 'dashboard':
    st.title("NeuroTwin: Many Ways to Thrive")
    st.write("### Your story. Your choices. Many Ways to thrive.")
    st.write("---")
    st.write("### Please select your preferred language:")
    
    # Native Language Buttons!
    display_langs = list(LANG_MAP.keys())
    cols = st.columns(4)
    for i, display_lang in enumerate(display_langs):
        if cols[i%4].button(display_lang, use_container_width=True):
            backend_lang = LANG_MAP[display_lang]
            st.session_state.lang = backend_lang
            st.session_state.responses['language'] = backend_lang
            st.session_state.current_step = 'pre_gate_1'
            st.rerun()
            
    st.divider()
    st.info("The NeuroTwin instrument uses the DMAP framework to map theoretical brain circuit topologies. Your data is strictly confidential and anonymized.")

# --- GATES ---
elif st.session_state.current_step == 'pre_gate_1':
    st.write("---")
    st.subheader(t["gate1_q"])
    col1, col2 = st.columns(2)
    if col1.button(t["gate1_yes"], use_container_width=True):
        st.session_state.current_step = 'pre_gate_2'
        st.rerun()
    if col2.button(t["gate1_no"], use_container_width=True):
        process_early_exit("Early Exit (Gate 1)")

elif st.session_state.current_step == 'pre_gate_2':
    st.write("---")
    st.warning(t["gate2_q"])
    col1, col2 = st.columns(2)
    if col1.button(t["gate2_yes"], use_container_width=True):
        st.session_state.current_step = 'dmap_part1'
        st.rerun()
    if col2.button(t["gate2_no"], use_container_width=True):
        process_early_exit("Early Exit (Gate 2)")

elif st.session_state.current_step == 'safe_exit':
    st.info(t["safe_exit_msg"])
    if st.button("Restart New Session"):
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
    st.write("**Narrative Reflection**")
    st.info(t["audio_hint"])
    
    st.write(t["t_narrative_1"])
    tn1_text = st.text_area("...", label_visibility="collapsed", key="tn1")
    tn1_audio = audio_recorder(key="mic_tn1", pause_threshold=300.0)
    
    st.write(t["t_narrative_2"])
    tn2_text = st.text_area("...", label_visibility="collapsed", key="tn2")
    tn2_audio = audio_recorder(key="mic_tn2", pause_threshold=300.0)

    if st.button(t["btn_continue"], type="primary"):
        st.session_state.responses.update({
            "t1": t1, "t2": t2, "t3": t3, "t4": t4, "t5": t5, "t6": t6, "t7": t7_raw,
            "threat_narrative_1": tn1_text, "threat_narrative_2": tn2_text
        })
        if tn1_audio: st.session_state.responses["threat_narrative_1_audio"] = save_audio_file(tn1_audio, "threat_narrative_1")
        if tn2_audio: st.session_state.responses["threat_narrative_2_audio"] = save_audio_file(tn2_audio, "threat_narrative_2")

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
        process_early_exit("Early Exit (Mid-Gate)")

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
    st.write("**Narrative Reflection**")
    st.info(t["audio_hint"])
    
    st.write(t["d_narrative_1"])
    dn1_text = st.text_area("...", label_visibility="collapsed", key="dn1")
    dn1_audio = audio_recorder(key="mic_dn1", pause_threshold=300.0)
    
    st.write(t["d_narrative_2"])
    dn2_text = st.text_area("...", label_visibility="collapsed", key="dn2")
    dn2_audio = audio_recorder(key="mic_dn2", pause_threshold=300.0)

    if st.button(t["btn_continue"], type="primary"):
        st.session_state.responses.update({
            "d1": d1, "d2": d2, "d3": d3, "d4": d4, "d5": d5, "d6": d6, "d7": d7_raw,
            "dep_narrative_1": dn1_text, "dep_narrative_2": dn2_text
        })
        if dn1_audio: st.session_state.responses["dep_narrative_1_audio"] = save_audio_file(dn1_audio, "dep_narrative_1")
        if dn2_audio: st.session_state.responses["dep_narrative_2_audio"] = save_audio_file(dn2_audio, "dep_narrative_2")

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
    st.info(t["audio_hint"])

    st.write(t["final_q1"])
    fn1_text = st.text_input("...", label_visibility="collapsed", key="fn1")
    fn1_audio = audio_recorder(key="mic_fn1", pause_threshold=300.0)

    st.write(t["final_q2"])
    fn2_text = st.text_input("...", label_visibility="collapsed", key="fn2")
    fn2_audio = audio_recorder(key="mic_fn2", pause_threshold=300.0)

    st.write(t["final_q3"])
    fn3_text = st.text_input("...", label_visibility="collapsed", key="fn3")
    fn3_audio = audio_recorder(key="mic_fn3", pause_threshold=300.0)

    st.divider()
    if st.button(t["btn_continue"], type="primary", use_container_width=True):
        st.session_state.responses.update({
            "final_narrative_1": fn1_text, "final_narrative_2": fn2_text, "final_narrative_3": fn3_text
        })
        if fn1_audio: st.session_state.responses["final_narrative_1_audio"] = save_audio_file(fn1_audio, "final_narrative_1")
        if fn2_audio: st.session_state.responses["final_narrative_2_audio"] = save_audio_file(fn2_audio, "final_narrative_2")
        if fn3_audio: st.session_state.responses["final_narrative_3_audio"] = save_audio_file(fn3_audio, "final_narrative_3")
        
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
        save_data_to_json() 
        
    st.success("Thank you. Your responses have been securely recorded.")
    
    if SHOW_RADAR_MAP:
        st.divider()
        t_score = st.session_state.responses.get("threat_score_avg", 0)
        d_score = st.session_state.responses.get("deprivation_score_avg", 0)
        w_score = st.session_state.responses.get("war_score_avg", 0)
        col_score = st.session_state.responses.get("col_score_avg", 3.0)
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Calculated Threat Index:** {t_score:.2f} / 5.0")
            st.write(f"**Calculated Deprivation Index:** {d_score:.2f} / 5.0")
        with col2:
            st.write(f"**Calculated War Index:** {w_score:.2f} / 5.0")
            st.write(f"**Collectivism Index:** {col_score:.2f} / 5.0")
        
        fig = generate_neurotwin_chart(t_score, d_score, w_score, col_score)
        st.pyplot(fig)
        
        st.divider()
        st.subheader("What does this mean?")
        st.write(
            "This radar chart maps your unique experiences onto theoretical brain circuits based on the **Dimensional Model of Adversity and Psychopathology (DMAP)**. "
            "Our brains are highly neuroplastic, meaning they physically adapt to the environments we grow up in to keep us safe."
        )
        
        if t_score > 3.0 or w_score > 3.0:
            st.markdown(
                "- **Threat Adaptations:** Your scores suggest your brain may have adapted to upregulate the *Salience Network* (regions like the Amygdala). "
                "This is an evolutionary superpower designed to keep you highly vigilant and safe in unpredictable environments."
            )
        if d_score > 3.0:
            st.markdown(
                "- **Deprivation Adaptations:** Your Deprivation Index indicates adaptations in the *Frontoparietal Control and Reward Networks*. "
                "This often reflects how the brain learns to conserve energy and find motivation when external resources or support were scarce."
            )
            
        if col_score > 3.0:
            st.markdown(
                "- **Cultural Buffering:** You scored higher in community-oriented values. "
                "Research suggests this interdependent worldview heavily engages the *Default Mode Network* (social cognition), meaning you likely process past adversity through the lens of community survival rather than isolation."
            )
            
        st.info(
            "**Remember:** A 'shifted' topology is not a damaged brain; it is an adapted brain. "
            "Just as the brain adapts to past adversity, it continues to rewire itself through new, safe, and culturally supportive experiences."
        )
