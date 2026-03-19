import streamlit as st
import pandas as pd
from datetime import datetime

# 기초 데이터 설정 [cite: 12, 48, 804]
st.set_page_config(page_title="인천 기초학력 검사", layout="wide")

# 세션 상태 초기화 (점수 저장용)
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'current_q' not in st.session_state:
    st.session_state.current_q = 0

st.title("🏫 기초학력 이음 지원단 검사 도구")

# 사이드바 설정 
with st.sidebar:
    name = st.text_input("학생 성함(가명)")
    grade = st.selectbox("학년", ["1학년", "2학년", "3학년", "4학년 이상"])
    subject = st.radio("검사 영역", ["9 이하 덧셈", "무의미 단어 읽기"])
    if st.button("검사 초기화"):
        st.session_state.score = 0
        st.session_state.current_q = 0
        st.rerun()

# 수학 문항 데이터 (PDF 7페이지 기준) [cite: 82-122]
math_qs = ["2+1", "1+4", "1+1", "3+2", "3+1", "5+0", "1+3", "4+1", "0+3", "6+1", 
           "1+5", "6+2", "8+1", "3+3", "4+4", "2+4", "4+3", "4+5", "3+5", "2+7",
           "2+6", "5+4", "1+6", "3+4", "7+1", "6+3", "5+3", "5+2", "4+2", "7+2"]

if name:
    st.info(f"대상 학생: {name} ({grade})")
    
    # 검사 화면
    if st.session_state.current_q < len(math_qs):
        q = math_qs[st.session_state.current_q]
        st.header(f"문제 {st.session_state.current_q + 1}: {q}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⭕ 정답 (맞음)", use_container_width=True):
                st.session_state.score += 1
                st.session_state.current_q += 1
                st.rerun()
        with col2:
            if st.button("❌ 오답 (틀림)", use_container_width=True):
                st.session_state.current_q += 1
                st.rerun()
    else:
        st.success("🎉 모든 검사가 완료되었습니다!")
        # 도달 판정 로직 
        threshold = 18 if grade in ["1학년", "2학년"] else 24
        result = "도달" if st.session_state.score >= threshold else "미도달"
        
        st.metric("최종 점수", f"{st.session_state.score} / {len(math_qs)}")
        st.write(f"판정 결과: **{result}** (기준점수: {threshold}점)")
        
        # 엑셀 다운로드용 데이터 생성 
        df = pd.DataFrame([{"날짜": datetime.now(), "이름": name, "학년": grade, "점수": st.session_state.score, "결과": result}])
        st.download_button("📊 결과 엑셀로 받기", df.to_csv(index=False).encode('utf-8-sig'), "result.csv", "text/csv")
else:
    st.warning("왼쪽 사이드바에 학생 이름을 입력하면 검사가 시작됩니다.")
