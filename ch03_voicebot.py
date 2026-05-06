import streamlit as st
from audiorecorder import audiorecorder
import openai
import os
from datetime import datetime
from gtts import gTTS
import base64

##### 기능 함수 #####

def STT(audio, apikey):
    filename = "input.mp3"
    audio.export(filename, format="mp3")
    client = openai.OpenAI(api_key=apikey)
    with open(filename, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    os.remove(filename)
    return response.text


def ask_gpt(messages, model, apikey):
    client = openai.OpenAI(api_key=apikey)
    response = client.chat.completions.create(
        model=model,
        messages=messages
    )
    return response.choices[0].message.content


def TTS(text):
    filename = "output.mp3"
    tts = gTTS(text=text, lang="ko")
    tts.save(filename)
    with open(filename, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
        <audio autoplay>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """
        st.markdown(md, unsafe_allow_html=True)
    os.remove(filename)


##### 메인 #####
def main():

    if "chat" not in st.session_state:
        st.session_state["chat"] = []
    if "OPENAI_API" not in st.session_state:
        st.session_state["OPENAI_API"] = ""
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {"role": "system", "content": "25단어 이내 한국어로 답변해"}
        ]
    if "new_question" not in st.session_state:
        st.session_state["new_question"] = False

    st.set_page_config(page_title="AReum Health Assistant", layout="wide")

    # ── 글로벌 CSS ──────────────────────────────────────────
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800&family=Noto+Sans+KR:wght@400;500;600&display=swap');

        /* 전체 배경 */
        .stApp {
            background: linear-gradient(160deg, #fff8f0 0%, #fff0f5 50%, #fffde7 100%);
            font-family: 'Noto Sans KR', sans-serif;
        }

        /* 상단 공백 제거 */
        .stApp > header { display: none; }
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        .block-container {
            padding-top: 2rem !important;
        }

        /* 사이드바 */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #ff6b6b 0%, #ff8e53 60%, #ffb347 100%);
        }
        [data-testid="stSidebar"] * {
            color: #ffffff !important;
        }
        [data-testid="stSidebar"] .stTextInput input {
            background-color: rgba(255,255,255,0.25) !important;
            color: white !important;
            border: 1px solid rgba(255,255,255,0.5) !important;
            border-radius: 10px;
        }
        [data-testid="stSidebar"] .stTextInput input::placeholder {
            color: rgba(255,255,255,0.7) !important;
        }
        [data-testid="stSidebar"] .stButton button {
            background: rgba(255,255,255,0.25) !important;
            color: white !important;
            border: 2px solid rgba(255,255,255,0.6) !important;
            border-radius: 10px;
            width: 100%;
            font-weight: 600;
        }
        [data-testid="stSidebar"] .stButton button:hover {
            background: rgba(255,255,255,0.4) !important;
        }

        /* 메인 타이틀 */
        .main-title {
            font-family: 'Playfair Display', serif;
            font-size: 3rem;
            font-weight: 800;
            background: linear-gradient(90deg, #ff6b6b, #ff8e53, #ffb347);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1.2;
            margin-bottom: 4px;
        }

        .sub-caption {
            font-family: 'Noto Sans KR', sans-serif;
            color: #f4a261;
            font-size: 1rem;
            font-weight: 500;
            margin-bottom: 1.5rem;
            letter-spacing: 0.05em;
        }

        /* 카드 */
        .card {
            background: rgba(255,255,255,0.75);
            backdrop-filter: blur(12px);
            border-radius: 20px;
            padding: 28px;
            box-shadow: 0 8px 32px rgba(255, 107, 107, 0.1);
            border: 1px solid rgba(255,180,150,0.3);
        }

        /* 섹션 타이틀 */
        .section-title {
            font-family: 'Noto Sans KR', sans-serif;
            font-size: 1.15rem;
            font-weight: 700;
            color: #e05a2b;
            margin-bottom: 16px;
        }

        /* 전송 버튼 */
        div[data-testid="stButton"] > button {
            background: linear-gradient(90deg, #ff6b6b, #ff8e53) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 0.5rem 2rem !important;
            font-weight: 700 !important;
            font-size: 0.95rem !important;
            letter-spacing: 0.03em;
            box-shadow: 0 4px 15px rgba(255,107,107,0.4);
            transition: all 0.2s ease;
        }
        div[data-testid="stButton"] > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(255,107,107,0.5) !important;
        }

        /* 입력창 */
        .stTextInput input {
            border-radius: 12px !important;
            border: 2px solid #ffd4c2 !important;
            background: #fff9f7 !important;
            padding: 10px 14px !important;
            font-family: 'Noto Sans KR', sans-serif;
        }
        .stTextInput input:focus {
            border-color: #ff8e53 !important;
            box-shadow: 0 0 0 3px rgba(255,142,83,0.15) !important;
        }

        /* 채팅 버블 - 사용자 */
        .chat-user {
            background: linear-gradient(135deg, #fff0e6, #ffe4d6);
            border-radius: 16px 16px 16px 4px;
            padding: 12px 18px;
            margin: 8px 0;
            font-size: 0.92rem;
            color: #5a2d0c;
            border-left: 3px solid #ff8e53;
            line-height: 1.6;
        }

        /* 채팅 버블 - 봇 */
        .chat-bot {
            background: linear-gradient(135deg, #fff5f5, #ffe8f0);
            border-radius: 16px 16px 4px 16px;
            padding: 12px 18px;
            margin: 8px 0;
            font-size: 0.92rem;
            color: #5a0a2d;
            border-right: 3px solid #ff6b6b;
            text-align: right;
            line-height: 1.6;
        }

        /* 구분선 */
        .divider {
            border: none;
            border-top: 2px solid #ffd4c2;
            margin: 16px 0;
        }
        
        div[data-testid="column"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        
    </style>
    """, unsafe_allow_html=True)
   

    # ── 헤더 ────────────────────────────────────────────────
    st.markdown('<h1 class="main-title">🌸 AReum Health Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-caption">✨ 당신의 질문에 답하는 스마트 AI 비서</p>', unsafe_allow_html=True)
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ── 사이드바 ─────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### ⚙️ 설정")
        st.markdown("---")
        st.session_state["OPENAI_API"] = st.text_input(
            "🔑 OPENAI API 키", type="password"
        )
        st.markdown(" ")
        model = st.radio("🤖 모델 선택", ["gpt-4", "gpt-3.5-turbo"])
        st.markdown("---")
        if st.button("🔄 대화 초기화"):
            st.session_state["chat"] = []
            st.session_state["messages"] = [
                {"role": "system", "content": "25단어 이내 한국어로 답변해"}
            ]
            st.session_state["new_question"] = False

    # ── 메인 컬럼 ────────────────────────────────────────────
    col1, col2 = st.columns([1,1])

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p class="section-title">🎤 질문하기</p>', unsafe_allow_html=True)

        user_input = st.text_input(
            label="질문입력",
            placeholder="예: 허리 통증에 좋은 운동이 뭔가요?",
            label_visibility="collapsed"
        )

        if st.button("✉️ 전송"):
            if not st.session_state["OPENAI_API"]:
                st.warning("⚠️ API 키를 먼저 입력해주세요!")
            elif not user_input:
                st.warning("⚠️ 질문을 입력해주세요!")
            else:
                now = datetime.now().strftime("%H:%M")
                st.session_state["chat"].append(("user", now, user_input))
                st.session_state["messages"].append(
                    {"role": "user", "content": user_input}
                )
                st.session_state["new_question"] = True

        try:
            audio = audiorecorder("🎙️ 녹음 시작", "⏹️ 녹음 중...")
            if audio and audio.duration_seconds > 0:
                st.audio(audio.export().read())
                question = STT(audio, st.session_state["OPENAI_API"])
                now = datetime.now().strftime("%H:%M")
                st.session_state["chat"].append(("user", now, question))
                st.session_state["messages"].append(
                    {"role": "user", "content": question}
                )
                st.session_state["new_question"] = True
        except Exception:
            st.info("🎤 마이크 없음 — 텍스트로 질문해주세요")

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p class="section-title">💬 질문 / 답변</p>', unsafe_allow_html=True)

        if st.session_state["new_question"]:
            if st.session_state["OPENAI_API"]:
                with st.spinner("🤔 생각 중..."):
                    try:
                        response = ask_gpt(
                            st.session_state["messages"],
                            model,
                            st.session_state["OPENAI_API"]
                        )
                        now = datetime.now().strftime("%H:%M")
                        st.session_state["chat"].append(("bot", now, response))
                        st.session_state["messages"].append(
                            {"role": "assistant", "content": response}
                        )
                        TTS(response)
                    except Exception as e:
                        st.error(f"❌ GPT 오류: {e}")
            st.session_state["new_question"] = False

        for sender, time, message in st.session_state["chat"]:
            if sender == "user":
                st.markdown(
                    f'<div class="chat-user">🙋‍♀️ <b>{time}</b><br>{message}</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div class="chat-bot">🤖 <b>{time}</b><br>{message}</div>',
                    unsafe_allow_html=True
                )

        st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()