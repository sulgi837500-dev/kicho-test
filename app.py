import streamlit as st
import pandas as pd
from datetime import datetime
import time

# 1. 페이지 설정 및 초기화
st.set_page_config(page_title="인천광역시교육청 학습종합클리닉센터", layout="wide")

if 'results' not in st.session_state: st.session_state.results = []
if 'current_q' not in st.session_state: st.session_state.current_q = 0
if 'score' not in st.session_state: st.session_state.score = 0
if 'step' not in st.session_state: st.session_state.step = "setup"
if 'start_time' not in st.session_state: st.session_state.start_time = None

# 2. 제목 섹션 (PDF 표지 반영) [cite: 2-7, 754-762]
st.markdown("""
    <div style="text-align: center; background-color: #f0f4f8; padding: 20px; border-radius: 15px;">
        <h4 style="margin-bottom: 5px;">모든 학생의 학습성공을 지원하는</h4>
        <h1 style="color: #0D47A1; margin-top: 0px;">찾아가는 학습지원의 사전·사후 검사 도구</h1>
        <h3 style="color: #333;">인천광역시교육청 학습종합클리닉센터</h3>
        <hr>
    </div>
""", unsafe_allow_html=True)

# 3. 사이드바 설정 [cite: 37-42, 767, 1005]
with st.sidebar:
    st.header("📋 학생 정보 및 영역 선택")
    name = st.text_input("학생명 (가명)")
    grade = st.selectbox("학년", ["1학년", "2학년", "3학년", "4학년", "5학년", "6학년", "중등"])
    period = st.radio("검사 시기", ["사전", "사후"])
    st.divider()
    category = st.selectbox("검사 대영역", ["기초 수학 (연산 유창성)", "기초 국어 (읽기·쓰기 유창성)"])
    
    if "수학" in category:
        sub_category = st.selectbox("세부 항목", ["① 9 이하 덧셈", "② 9 이하 뺄셈", "③ 받아올림 덧셈", "④ 받아내림 뺄셈", "⑦ 곱셈구구(2~5단)", "⑧ 곱셈구구(6~9단)"])
        limit_sec = 60 # 수학은 각 영역당 1분 [cite: 74, 163, 322]
    else:
        sub_category = st.selectbox("세부 항목", ["② 무의미 단어 읽기 유창성", "③ 읽기 유창성 (설명문)"])
        limit_sec = 40 if "무의미" in sub_category else 60 # 무의미 40초 [cite: 831, 856]

    if st.button("🔄 검사 초기화"):
        st.session_state.step = "setup"; st.session_state.current_q = 0; st.session_state.score = 0
        st.session_state.results = []; st.session_state.start_time = None; st.rerun()

# 4. 전체 문항 데이터베이스 (PDF 전수 반영)
# [수학 문항: cite 82-123, 127-155, 170-200, 205-234, 330-359, 363-393]
# [국어 문항: cite 837, 863, 942-955]
math_addition_9 = ["2+1", "1+4", "1+1", "3+2", "3+1", "5+0", "1+3", "4+1", "0+3", "6+1", "1+5", "6+2", "8+1", "3+3", "4+4", "2+4", "4+3", "4+5", "3+5", "2+7", "2+6", "5+4", "1+6", "3+4", "7+1", "6+3", "5+3", "5+2", "4+2", "7+2"]
math_sub_9 = ["3-1", "2-1", "3-2", "5-2", "5-3", "3-3", "4-2", "5-4", "4-3", "6-1", "9-5", "8-4", "7-2", "8-5", "9-7", "8-7", "9-4", "9-2", "8-3", "7-0", "7-4", "7-5", "9-3", "7-6", "8-6", "8-1", "6-4", "8-2", "6-3", "9-6"]
math_add_up = ["9+1", "9+3", "7+3", "9+2", "8+2", "6+6", "3+8", "6+4", "2+9", "7+9", "6+8", "4+7", "6+5", "8+6", "9+4", "9+5", "4+8", "5+7", "8+9", "7+6", "4+9", "7+5", "5+9", "7+7", "9+7", "7+8", "9+9", "8+8", "5+8", "6+9"]
math_sub_down = ["10-1", "11-3", "10-5", "10-8", "12-3", "11-9", "12-4", "11-8", "11-2", "12-9", "13-6", "11-6", "13-5", "11-5", "18-9", "12-8", "15-8", "14-9", "14-7", "13-9", "13-7", "12-6", "11-7", "16-8", "12-7", "16-9", "14-8", "11-4", "15-6", "17-8"]
math_mul_low = ["3x1", "5x2", "2x2", "5x1", "4x2", "5x4", "2x3", "5x3", "2x4", "4x4", "3x3", "3x5", "4x5", "5x5", "2x6", "5x6", "2x7", "5x7", "2x8", "5x8", "2x9", "4x3", "3x7", "3x9", "4x8", "3x6", "4x9", "3x8", "4x6", "3x4"]
math_mul_high = ["6x1", "9x2", "8x2", "8x5", "9x1", "9x5", "6x5", "7x2", "7x5", "6x3", "9x4", "6x4", "7x3", "8x3", "9x3", "6x6", "8x4", "7x7", "7x4", "8x8", "9x7", "6x7", "8x9", "7x6", "6x9", "7x9", "8x6", "9x6", "6x8", "9x8"]

kor_nonsense = ["포모", "나버", "계난", "책성", "연팔", "펭권", "코끼러", "피마노", "교과사", "강어지", "다람쥐", "놀미터", "동화챈", "일기창", "경철서", "달팽미", "발차국", "준비물", "운동정", "우리너라", "해바리기", "할아비지", "따라좁기", "동그라무", "바디표범", "딱따구리", "체육대화", "초등학고", "확실히게", "숨바꼬질", "미끄럼톨", "국어서전", "징감다리", "특별화동", "동시남분", "실험관칠", "고속타미달", "이산화탐소", "현장체험학습", "한국전동문회"]
kor_passage = ["땀이 나는 이유", "여러분,", "땀을", "흘려", "본", "경험이", "있지요?", "우리는", "여러", "가지", "상황에서", "땀을", "흘립니다.", "땀은", "왜", "나는", "것일까요?", "그 이유는", "첫째,", "우리 몸의", "온도를", "일정하게", "유지하기", "위해서입니다."]

# 선택 항목에 따른 문항 매칭
q_map = {
    "① 9 이하 덧셈": math_addition_9, "② 9 이하 뺄셈": math_sub_9,
    "③ 받아올림 덧셈": math_add_up, "④ 받아내림 뺄셈": math_sub_down,
    "⑦ 곱셈구구(2~5단)": math_mul_low, "⑧ 곱셈구구(6~9단)": math_mul_high,
    "② 무의미 단어 읽기 유창성": kor_nonsense, "③ 읽기 유창성 (설명문)": kor_passage
}
questions = q_map.get(sub_category, [])

# 5. 검사 실행 로직
if not name:
    st.warning("👈 왼쪽 사이드바에서 학생 정보를 입력하세요.")
elif st.session_state.step == "setup":
    st.subheader(f"📢 {sub_category} 안내")
    st.info("지우개는 사용하지 않습니다. 선생님이 '시작'이라고 하면 최대한 빠르고 정확하게 수행하세요.")
    if st.button("검사 시작", type="primary"):
        st.session_state.start_time = time.time(); st.session_state.step = "test"; st.rerun()

elif st.session_state.step == "test":
    elapsed = time.time() - st.session_state.start_time
    rem = max(0, limit_sec - int(elapsed))
    st.progress(rem / limit_sec, text=f"⏱️ 남은 시간: {rem}초")
    
    if rem <= 0 or st.session_state.current_q >= len(questions):
        st.error("⏰ 종료되었습니다!"); st.session_state.step = "result"; st.button("결과 분석 보기"); st.stop()

    q = questions[st.session_state.current_q]
    st.markdown(f"<h1 style='text-align: center; font-size: 100px;'>{q}</h1>", unsafe_allow_html=True)

    with st.expander("📝 관찰 기록", expanded=True):
        speed = st.radio("반응 속도", ["즉각적", "느림/주저함"], horizontal=True)
        note = st.text_input("특이사항 (오독 내용 등)")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("⭕ 정답", use_container_width=True, type="primary"):
            st.session_state.results.append({"번호": st.session_state.current_q+1, "문항": q, "정오": "정답", "속도": speed, "비고": note})
            st.session_state.score += 1; st.session_state.current_q += 1; st.rerun()
    with c2:
        if st.button("❌ 오답", use_container_width=True):
            st.session_state.results.append({"번호": st.session_state.current_q+1, "문항": q, "정오": "오답", "속도": speed, "비고": note})
            st.session_state.current_q += 1; st.rerun()

elif st.session_state.step == "result":
    # 도달 기준 판정 (PDF 기준 반영) 
    if "덧셈" in sub_category: threshold = 18 if grade in ["1학년", "2학년"] else 24
    elif "뺄셈" in sub_category: threshold = 13 if grade in ["1학년", "2학년"] else 19
    elif "무의미" in sub_category:
        m_map = {"1학년": 17, "2학년": 21, "3학년": 19, "4학년": 22, "5학년": 22, "6학년": 22, "중등": 22}
        threshold = m_map.get(grade, 22)
    else: threshold = 15 # 기본값
    
    st.header("📊 진단 보고서 요약")
    status = "도달" if st.session_state.score >= threshold else "미도달"
    st.metric(f"{sub_category} 최종 점수", f"{st.session_state.score}점", f"판정 결과: {status} (기준: {threshold}점)")
    
    df = pd.DataFrame(st.session_state.results)
    st.table(df)
    
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 엑셀 결과 저장", csv, f"{name}_{sub_category}_결과.csv")

st.markdown("<br><hr><center>© 인천광역시교육청 학습종합클리닉센터</center>", unsafe_allow_html=True)
