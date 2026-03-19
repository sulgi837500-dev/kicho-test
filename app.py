import streamlit as st
import pandas as pd
from datetime import datetime
import time

# 1. 웹 페이지 기본 설정
st.set_page_config(page_title="인천광역시교육청 학습종합클리닉센터", layout="wide")

# 2. 세션 상태 초기화
if 'results' not in st.session_state: st.session_state.results = [] 
if 'current_q' not in st.session_state: st.session_state.current_q = 0
if 'score' not in st.session_state: st.session_state.score = 0
if 'step' not in st.session_state: st.session_state.step = "setup"
if 'start_time' not in st.session_state: st.session_state.start_time = None

# 3. 제목 섹션
st.markdown("""
    <div style="text-align: center; background-color: #e3f2fd; padding: 20px; border-radius: 10px;">
        <h4 style="margin-bottom: 5px;">모든 학생의 학습성공을 지원하는</h4>
        <h2 style="color: #0D47A1; margin-top: 0px;">찾아가는 학습지원의 사전·사후 검사 도구</h2>
        <h3 style="color: #333;">인천광역시교육청 학습종합클리닉센터</h3>
        <hr>
    </div>
    """, unsafe_allow_html=True)

# 4. 사이드바 설정
with st.sidebar:
    st.header("📋 학생 정보 입력")
    name = st.text_input("학생명 (가명)", placeholder="이름 입력")
    grade = st.selectbox("학년", ["1학년", "2학년", "3학년", "4학년", "5학년", "6학년", "중등"])
    period = st.radio("검사 시기", ["사전", "사후"])
    st.divider()
    main_category = st.selectbox("검사 영역", ["기초 수학", "기초 국어"])
    
    # 수학 세부 항목 및 제한 시간 설정
    if main_category == "기초 수학":
        sub_category = st.selectbox("세부 항목", ["① 9 이하 덧셈", "② 9 이하 뺄셈", "③ 받아올림 덧셈", "④ 받아내림 뺄셈", "⑤ 두 자리 수 덧셈", "⑥ 두 자리 수 뺄셈", "⑦ 곱셈구구(2~5단)", "⑧ 곱셈구구(6~9단)"])
        limit_sec = 120 if "두 자리" in sub_category else 60 # 두 자리는 2분, 나머지는 1분
    else:
        sub_category = st.selectbox("세부 항목", ["② 무의미 단어 읽기 유창성"])
        limit_sec = 40

    if st.button("🔄 검사 초기화"):
        st.session_state.step = "setup"; st.session_state.current_q = 0
        st.session_state.score = 0; st.session_state.results = []
        st.session_state.start_time = None; st.rerun()

# 5. 문항 데이터 (영상 및 PDF 반영)
math_addition_9 = ["2+1", "1+4", "1+1", "3+2", "3+1", "5+0", "1+3", "4+1", "0+3", "6+1"]
math_subtraction_9 = ["3-1", "2-1", "3-2", "5-2", "5-3", "3-3", "4-2", "5-4", "4-3", "6-1"]
math_multi_high = ["6x1", "9x2", "8x2", "8x5", "9x1", "9x5", "6x5", "7x2", "7x5", "6x3"] # 6~9단

if "9 이하 덧셈" in sub_category: questions = math_addition_9
elif "9 이하 뺄셈" in sub_category: questions = math_subtraction_9
elif "6~9단" in sub_category: questions = math_multi_high
else: questions = ["포모", "나버", "계난", "책성", "연팔"] # 예시

# 6. 단계별 실행
if not name:
    st.warning("👈 왼쪽에서 학생 정보를 입력해 주세요.")

# [STEP 1: 안내 및 준비]
elif st.session_state.step == "setup":
    st.subheader("📢 검사 준비 및 안내")
    st.markdown(f"""
    **[학생 안내 사항]**
    1. 선생님이 '시작'이라고 하면 최대한 빠르고 정확하게 답합니다.
    2. **지우개는 사용하지 않습니다.** (고치고 싶다면 바로 다시 말하세요.)
    3. 제한 시간: **{limit_sec}초**
    """)
    if st.button("시작 (타이머 작동)", type="primary"):
        st.session_state.start_time = time.time()
        st.session_state.step = "test"; st.rerun()

# [STEP 2: 실시간 검사 및 타이머]
elif st.session_state.step == "test":
    elapsed = time.time() - st.session_state.start_time
    remaining = max(0, limit_sec - int(elapsed))
    
    st.progress(remaining / limit_sec, text=f"남은 시간: {remaining}초")
    
    if remaining <= 0 or st.session_state.current_q >= len(questions):
        st.warning("시간 종료 또는 모든 문항 완료!")
        if st.button("결과 확인"): st.session_state.step = "result"; st.rerun()
    else:
        q = questions[st.session_state.current_q]
        st.markdown(f"<h1 style='font-size: 120px; text-align: center; color: #1565C0;'>{q}</h1>", unsafe_allow_html=True)
        
        # 질적 기록 (반응 속도 및 오답 유형)
        with st.expander("📝 관찰 기록 (반응 속도 및 전략)", expanded=True):
            speed = st.radio("반응 속도", ["즉각적", "머뭇거림/손가락셈"], horizontal=True)
            note = st.text_input("오답 내용 또는 특이 행동", placeholder="예: 거꾸로 세기 사용")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("⭕ 정답", use_container_width=True, type="primary"):
                st.session_state.results.append({"번호": st.session_state.current_q+1, "문항": q, "정오": "정답", "속도": speed, "비고": note})
                st.session_state.score += 1; st.session_state.current_q += 1; st.rerun()
        with c2:
            if st.button("❌ 오답", use_container_width=True):
                st.session_state.results.append({"번호": st.session_state.current_q+1, "문항": q, "정오": "오답", "속도": speed, "비고": note})
                st.session_state.current_q += 1; st.rerun()

# [STEP 3: 결과 분석 및 엑셀]
elif st.session_state.step == "result":
    st.header("📊 검사 결과 보고서")
    # 도달 기준 자동 판정
    if "9 이하 덧셈" in sub_category: threshold = 18 if grade in ["1학년", "2학년"] else 24
    elif "9 이하 뺄셈" in sub_category: threshold = 13 if grade in ["1학년", "2학년"] else 19
    else: threshold = 15 # 기본값
    
    status = "도달" if st.session_state.score >= threshold else "미도달"
    st.metric(f"{sub_category} 결과", f"{st.session_state.score}점", f"판정: {status} (기준: {threshold}점)")
    
    df = pd.DataFrame(st.session_state.results)
    st.table(df)
    
    # 엑셀 다운로드
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 엑셀 결과 저장", csv, f"{name}_수학검사_결과.csv", "text/csv")

st.markdown("<br><hr><center>© 인천광역시교육청 학습종합클리닉센터 (초등교육과)</center>", unsafe_allow_html=True)
