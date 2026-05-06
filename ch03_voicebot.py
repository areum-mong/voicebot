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

    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800&family=Noto+Sans+KR:wght@400;500;600&display=swap');

        .stApp {
            background: linear-gradient(160deg, #fff8f0 0%, #fff0f5 50%, #fffde7 100%);
            font-family: 'Noto Sans KR', sans-serif;
        }
        .stApp > header { display: none; }
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        .block-container { padding-top: 2rem !important; }

        /* 사이드바 */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #ff6b6b 0%, #ff8e53 60%, #ffb347 100%);
        }
        [data-testid="stSidebar"] * { color: #ffffff !important; }
        [data-testid="stSidebar"] .stTextInput input {
            background-color: rgba(255,255,255,0.92) !important;
            color: #222222 !important;
            -webkit-text-fill-color: #222222 !important;
            border: 2px solid rgba(255,255,255,0.8) !important;
            border-radius: 10px;
        }
        [data-testid="stSidebar"] .stTextInput input::placeholder {
            color: #aaaaaa !important;
            -webkit-text-fill-color: #aaaaaa !important;
        }
        [data-testid="stSidebar"] .stTextInput label {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
        }
        [data-testid="stSidebar"] button[aria-label="Show password text"] svg,
        [data-testid="stSidebar"] button[aria-label="Hide password text"] svg {
            fill: #888888 !important;
            stroke: #888888 !important;
        }
        [data-testid="stSidebar"] .stButton button {
            background: rgba(255,255,255,0.25) !important;
            color: white !important;
            border: 2px solid rgba(255,255,255,0.6) !important;
            border-radius: 10px;
            width: 100%;
            font-weight: 600;
        }

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
            color: #f4a261;
            font-size: 1rem;
            font-weight: 500;
            margin-bottom: 1rem;
        }

        /* 카드 - height: 100% 제거하여 빈 공간 방지 */
        .card {
            background: rgba(255,255,255,0.75);
            backdrop-filter: blur(12px);
            border-radius: 20px;
            padding: 24px 28px;
            box-shadow: 0 8px 32px rgba(255,107,107,0.1);
            border: 1px solid rgba(255,180,150,0.3);
            margin-bottom: 1rem;
        }
        .section-title {
            font-size: 1.1rem;
            font-weight: 700;
            color: #e05a2b;
            margin-bottom: 14px;
        }

        /* 팁 박스 */
        .tip-box {
            background: linear-gradient(135deg, #fff3e0, #ffe0b2);
            border-radius: 12px;
            padding: 14px 16px;
            border-left: 4px solid #ff8e53;
            font-size: 0.88rem;
            color: #6d3a00;
            line-height: 1.7;
            margin-top: 8px;
        }
        .tip-title {
            font-weight: 700;
            font-size: 0.95rem;
            color: #e05a2b;
            margin-bottom: 6px;
        }

        /* 버튼 */
        div[data-testid="stButton"] > button {
            background: linear-gradient(90deg, #ff6b6b, #ff8e53) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 0.5rem 2rem !important;
            font-weight: 700 !important;
            font-size: 0.95rem !important;
            box-shadow: 0 4px 15px rgba(255,107,107,0.35);
        }

        /* 텍스트 입력창 */
        .stTextInput input {
            border-radius: 12px !important;
            border: 2px solid #ffd4c2 !important;
            background: #fff9f7 !important;
            padding: 10px 14px !important;
        }

        /* 채팅 버블 */
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
        .divider {
            border: none;
            border-top: 2px solid #ffd4c2;
            margin: 20px 0;
        }
        div[data-testid="column"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # ── 사이드바 ─────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### ⚙️ 설정")
        st.markdown("---")
        api_input = st.text_input("🔑 OPENAI API 키", type="password", placeholder="sk-...")
        if api_input:
            st.session_state["OPENAI_API"] = api_input
            st.success("✅ API 키 입력됨")
        st.markdown(" ")
        model = st.radio("🤖 모델 선택", ["gpt-4o", "gpt-4", "gpt-3.5-turbo"])
        st.markdown("---")
        if st.button("🔄 대화 초기화"):
            st.session_state["chat"] = []
            st.session_state["messages"] = [{"role": "system", "content": "25단어 이내 한국어로 답변해"}]
            st.session_state["new_question"] = False

    # ── 헤더 ────────────────────────────────────────────────
    st.markdown('<h1 class="main-title">🌸 AReum Health Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-caption">✨ 당신의 질문에 답하는 스마트 AI 비서</p>', unsafe_allow_html=True)
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ── 1행: 음성입력(좌) + 사용팁(우) ───────────────────────
    col_voice, col_tip = st.columns([1, 1])

    with col_voice:
        # 스트림릿 위젯(녹음기)은 HTML <div> 태그로 감쌀 수 없으므로 제목만 표시합니다.
        st.markdown('<p class="section-title">🎙️ 음성으로 질문하기</p>', unsafe_allow_html=True)
        try:
            audio = audiorecorder(
                start_prompt="🔴 녹음 시작",
                stop_prompt="⏹️ 녹음 끝",
                pause_prompt="",
                show_visualizer=False,
            )
            if len(audio) > 0 and audio.duration_seconds > 0:
                st.audio(audio.export().read())
                if not st.session_state["OPENAI_API"]:
                    st.warning("⚠️ API 키를 입력해주세요!")
                else:
                    with st.spinner("🔄 음성 변환 중..."):
                        question = STT(audio, st.session_state["OPENAI_API"])
                    st.success(f"📝 인식: **{question}**")
                    now = datetime.now().strftime("%H:%M")
                    st.session_state["chat"].append(("user", now, question))
                    st.session_state["messages"].append({"role": "user", "content": question})
                    st.session_state["new_question"] = True
        except Exception:
            st.info("🎤 마이크 없음 — 아래 텍스트로 질문해주세요")

    with col_tip:
        # 텍스트 요소들은 하나의 HTML 문자열로 합쳐서 카드 안에 쏙 들어가게 만듭니다.
        tip_html = """
        <div class="card">
            <p class="section-title">💡 이렇게 사용해보세요</p>
            <div class="tip-box">
                <div class="tip-title">🎙️ 음성 질문 팁</div>
                마이크 버튼을 누른 후 또렷하게 말하고<br>
                녹음 끝 버튼을 눌러주세요.<br><br>
                <div class="tip-title">✉️ 텍스트 질문 팁</div>
                아래 입력창에 질문을 입력하고<br>
                전송 버튼을 눌러주세요.<br><br>
                <div class="tip-title">🩺 추천 질문 예시</div>
                • 허리 통증에 좋은 스트레칭은?<br>
                • 무릎 재활 운동 알려줘<br>
                • 어깨 충돌증후군 관리법은?
            </div>
        </div>
        """
        st.markdown(tip_html, unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ── 2행: 텍스트입력(좌) + 답변(우) ───────────────────────
    col_text, col_answer = st.columns([1, 1])

    with col_text:
        # 텍스트 입력창 역시 파이썬 위젯이므로 오류 방지를 위해 박스를 씌우지 않고 제목만 배치합니다.
        st.markdown('<p class="section-title">✉️ 텍스트로 질문하기</p>', unsafe_allow_html=True)
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
                st.session_state["messages"].append({"role": "user", "content": user_input})
                st.session_state["new_question"] = True

    with col_answer:
        # GPT 모델이 답변을 생성하는 부분
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
                        st.session_state["messages"].append({"role": "assistant", "content": response})
                        TTS(response)
                    except Exception as e:
                        st.error(f"❌ GPT 오류: {e}")
            st.session_state["new_question"] = False

        # 채팅 기록을 하나의 긴 HTML 카드로 묶어서 출력 (박스 안에 글자가 들어가도록 처리)
        chat_html = '<div class="card">\n<p class="section-title">💬 질문 / 답변</p>\n'
        
        if not st.session_state["chat"]:
            chat_html += '<div style="text-align:center; color:#ffb89a; padding: 30px 0; font-size:0.95rem;">🌸 질문을 입력하면<br>여기에 답변이 표시됩니다</div>'
        else:
            for sender, time, message in st.session_state["chat"]:
                if sender == "user":
                    chat_html += f'<div class="chat-user">🙋‍♀️ <b>{time}</b><br>{message}</div>\n'
                else:
                    chat_html += f'<div class="chat-bot">🤖 <b>{time}</b><br>{message}</div>\n'
        
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
