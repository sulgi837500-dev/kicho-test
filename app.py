import streamlit as st
import pandas as pd
from datetime import datetime
import time

# 1. 페이지 설정
st.set_page_config(page_title="인천광역시교육청 학습종합클리닉센터", layout="wide")

if 'results' not in st.session_state: st.session_state.results = []
if 'current_q' not in st.session_state: st.session_state.current_q = 0
if 'score' not in st.session_state: st.session_state.score = 0
if 'step' not in st.session_state: st.session_state.step = "setup"
if 'start_time' not in st.session_state: st.session_state.start_time = None

# 2. 제목 섹션 [cite: 754-762, 992-1000]
st.markdown("""
    <div style="text-align: center; background-color: #f0f4f8; padding: 20px; border-radius: 15px;">
        <h4 style="margin-bottom: 5px;">모든 학생의 학습성공을 지원하는</h4>
        <h1 style="color: #0D47A1; margin-top: 0px;">찾아가는 학습지원의 사전·사후 검사 도구</h1>
        <h3 style="color: #333;">인천광역시교육청 학습종합클리닉센터</h3>
        <hr>
    </div>
""", unsafe_allow_html=True)

# 3. 사이드바 설정 (초1~고3 확장)
with st.sidebar:
    st.header("📋 검사 설정")
    name = st.text_input("학생명 (가명)")
    
    # 학년 선택 범위 확장
    grade_options = [f"초등 {i}학년" for i in range(1, 7)] + [f"중등 {i}학년" for i in range(1, 4)] + [f"고등 {i}학년" for i in range(1, 4)]
    grade = st.selectbox("학생 학년", grade_options)
    
    is_secondary = "중등" in grade or "고등" in grade
    
    period = st.radio("검사 시기", ["사전", "사후"])
    st.divider()
    category = st.selectbox("대영역", ["기초 국어 (읽기·쓰기 유창성)", "기초 수학 (연산 유창성)"])
    
    if "국어" in category:
        # 중등 이상일 경우 '읽기 이해' 항목 추가 
        kor_items = ["① 한글 해득 수준", "② 무의미 단어 읽기 유창성", "③ 읽기 유창성 (설명문)"]
        if is_secondary:
            kor_items.append("④ 읽기 이해 (단어 선택)")
        sub_category = st.selectbox("세부 항목", kor_items)
        limit_sec = 120 if "이해" in sub_category else (40 if "무의미" in sub_category else 60)
    else:
        sub_category = st.selectbox("세부 항목", ["① 9 이하 덧셈", "② 9 이하 뺄셈", "③ 받아올림 덧셈", "④ 받아내림 뺄셈", "⑦ 곱셈구구"])
        limit_sec = 60

    if st.button("🔄 전체 초기화"):
        st.session_state.step = "setup"; st.session_state.current_q = 0; st.session_state.score = 0
        st.session_state.results = []; st.session_state.start_time = None; st.rerun()

# 4. 문항 데이터 (중등 문항 추가) [cite: 1154, 1266, 1295]
math_addition_9 = ["2+1", "1+4", "1+1", "3+2", "3+1", "5+0", "1+3", "4+1", "0+3", "6+1"] 

# 중등 전용: 읽기 유창성 지문 [cite: 1154-1156]
secondary_passage = ["반려동물", "관련", "직업", "세계(제목)", "사람과", "더불어", "살아가기", "위한", "목적으로", "기르는", "동물을", "반려동물이라고", "합니다."]

# 중등 전용: 읽기 이해 (단어 선택) [cite: 1267-1269]
secondary_comprehension = [
    {"text": "사람과 인공지능의 대결은 사람들의 많은 관심을", "options": ["받아왔습니다", "선물", "상쾌한"], "answer": "받아왔습니다"},
    {"text": "과연 인공지능이 사람을 이길 수 있을까요?", "options": ["개인적인", "대표적인", "긍정적인"], "answer": "대표적인"}
]

if "이해" in sub_category:
    questions = secondary_comprehension
elif "설명문" in sub_category and is_secondary:
    questions = secondary_passage
elif "무의미" in sub_category:
    # 3학년 이상은 48문항 전제 [cite: 856, 1071]
    questions = ["포모", "나버", "계난", "책성", "연팔", "펭권", "코끼러", "피마노", "교과사", "강어지"] * 5 
else:
    questions = math_addition_9

# 5. 검사 로직
if not name:
    st.warning("👈 왼쪽에서 학생 정보를 입력하세요.")
elif st.session_state.step == "setup":
    st.subheader(f"📢 {sub_category} 안내")
    if "이해" in sub_category:
        st.info("글을 읽으면서 괄호 안의 세 단어 중 알맞은 단어를 고르세요. 제한 시간은 2분입니다.") [cite: 1232, 1239]
    else:
        st.info("최대한 빠르고 정확하게 수행합니다. 지우개는 사용하지 않습니다.")
    if st.button("검사 시작", type="primary"):
        st.session_state.start_time = time.time(); st.session_state.step = "test"; st.rerun()

elif st.session_state.step == "test":
    elapsed = time.time() - st.session_state.start_time
    rem = max(0, limit_sec - int(elapsed))
    st.progress(rem / limit_sec, text=f"⏱️ 남은 시간: {rem}초")
    
    if rem <= 0 or st.session_state.current_q >= len(questions):
        st.session_state.step = "result"; st.rerun()

    q = questions[st.session_state.current_q]
    
    # 단어 선택 검사(중등) UI 
    if "이해" in sub_category:
        st.markdown(f"### {q['text']}")
        cols = st.columns(3)
        for idx, opt in enumerate(q['options']):
            if cols[idx].button(opt, use_container_width=True):
                is_correct = "정답" if opt == q['answer'] else "오답"
                st.session_state.results.append({"번호": st.session_state.current_q+1, "선택": opt, "정오": is_correct})
                if opt == q['answer']: st.session_state.score += 1
                st.session_state.current_q += 1; st.rerun()
    else:
        st.markdown(f"<h1 style='text-align: center; font-size: 80px;'>{q}</h1>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("⭕ 정답", use_container_width=True, type="primary"):
                st.session_state.results.append({"번호": st.session_state.current_q+1, "문항": q, "정오": "정답"})
                st.session_state.score += 1; st.session_state.current_q += 1; st.rerun()
        with c2:
            if st.button("❌ 오답", use_container_width=True):
                st.session_state.results.append({"번호": st.session_state.current_q+1, "문항": q, "정오": "오답"})
                st.session_state.current_q += 1; st.rerun()

elif st.session_state.step == "result":
    # 도달 기준 
    threshold = 22 if "이해" in sub_category else 15
    status = "도달" if st.session_state.score >= threshold else "미도달"
    st.header("📊 진단 결과")
    st.metric("최종 점수", f"{st.session_state.score}점", f"판정: {status}")
    
    df = pd.DataFrame(st.session_state.results)
    st.table(df)
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 엑셀 저장", csv, f"{name}_결과.csv")

st.markdown("<br><hr><center>© 인천광역시교육청 학습종합클리닉센터</center>", unsafe_allow_html=True)
