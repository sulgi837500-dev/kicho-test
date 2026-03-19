import os
import sys
import subprocess

# 라이브러리 미설치 시 자동 설치 로직
try:
    import xlsxwriter
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "xlsxwriter"])

import streamlit as st
import pandas as pd
from datetime import datetime
import time
import io

# 1. 페이지 및 세션 초기화
st.set_page_config(page_title="인천광역시교육청 학습종합클리닉센터", layout="wide")

keys = {
    'results': [], 'current_q': 0, 'score': 0, 'step': "setup",
    'start_time': None, 'path_step': "1단계: 모음", 'level_score': 0,
    'total_read_count': 0, 'error_count': 0
}
for key, val in keys.items():
    if key not in st.session_state:
        st.session_state[key] = val

# 2. 제목 섹션 [cite: 754-762]
st.markdown("""
    <div style="text-align: center; background-color: #f0f4f8; padding: 20px; border-radius: 15px; border: 1px solid #d1d9e6;">
        <h4 style="margin-bottom: 5px;">모든 학생의 학습성공을 지원하는</h4>
        <h1 style="color: #0D47A1; margin-top: 0px;"> 학습지원 학생의 사전·사후 검사 도구</h1>
        <h3 style="color: #333;">인천광역시교육청 학습종합클리닉센터</h3>
    </div>
""", unsafe_allow_html=True)

# 3. 데이터베이스 (PDF 전수 반영) [cite: 83-393, 767, 794-803, 942, 1155]
hangeul_qs = {
    "1단계: 모음": ["ㅏ", "ㅓ", "ㅗ", "ㅜ", "ㅡ", "ㅣ", "ㅐ", "ㅔ", "ㅑ", "ㅕ"],
    "2단계: 자음": ["ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ", "ㄲ", "ㄸ", "ㅃ", "ㅆ", "ㅉ"],
    "3단계: 받침 없는 글자": ["가", "나", "다", "라", "마", "바", "사", "아", "자", "차", "카", "타", "파", "하"],
    "4단계: 받침 없는 단어": ["아파", "거미", "효자", "라디오", "배나무", "프소", "가야", "유하", "묘시", "녀타"]
}

# 4. 검사 로직
with st.sidebar:
    name = st.text_input("학생명 (가명)")
    grade = st.selectbox("학년", [f"초등 {i}학년" for i in range(1, 7)] + [f"중등 {i}학년" for i in range(1, 4)])
    if st.button("🔄 전체 초기화"):
        for k, v in keys.items(): st.session_state[k] = v
        st.rerun()

if not name:
    st.warning("👈 학생 정보를 입력하세요.")
elif st.session_state.step == "setup":
    st.subheader(f"📍 {name} 학생 진단")
    if st.button("📖 한글 해득 진단 시작"):
        st.session_state.step = "h_test"; st.rerun()

elif st.session_state.step == "h_test":
    qs = hangeul_qs[st.session_state.path_step]
    q = qs[st.session_state.current_q]
    st.markdown(f"<h1 style='text-align: center; font-size: 150px;'>{q}</h1>", unsafe_allow_html=True)
    
    with st.expander("📝 질적 분석 기록", expanded=True):
        speed = st.radio("반응 속도", ["즉각적", "느림"], horizontal=True, key=f"s_{st.session_state.current_q}")
        actual = st.text_input("아동 발화", key=f"a_{st.session_state.current_q}")

    c1, c2 = st.columns(2)
    if c1.button("⭕ 정답", use_container_width=True):
        st.session_state.results.append({"번호": st.session_state.current_q+1, "보기": q, "목표": q, "아동반응": actual if actual else q, "속도": speed, "점수": 1})
        st.session_state.level_score += 1; st.session_state.current_q += 1
        if st.session_state.current_q >= len(qs): st.session_state.step = "h_res"
        st.rerun()
    if c2.button("❌ 오답", use_container_width=True):
        st.session_state.results.append({"번호": st.session_state.current_q+1, "보기": q, "목표": q, "아동반응": actual, "속도": speed, "점수": 0})
        st.session_state.current_q += 1
        if st.session_state.current_q >= len(qs): st.session_state.step = "h_res"
        st.rerun()

elif st.session_state.step == "h_res":
    if st.session_state.level_score == len(hangeul_qs[st.session_state.path_step]):
        st.success("✅ 통과!"); levels = list(hangeul_qs.keys()); idx = levels.index(st.session_state.path_step)
        if idx + 1 < len(levels) and st.button("다음 레벨"):
            st.session_state.update({"path_step": levels[idx+1], "current_q": 0, "level_score": 0, "step": "h_test"}); st.rerun()
    else:
        st.error("❌ 미도달"); st.button("저장 및 종료", on_click=lambda: st.session_state.update({"step": "final"}))

# 5. 진단 데이터 저장 (이미지 양식 반영)
elif st.session_state.step == "final":
    st.subheader("📁 진단 데이터 저장")
    df = pd.DataFrame(st.session_state.results)
    output = io.BytesIO()
    # 엔진을 명시적으로 지정
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='질적분석', index=False)
    
    st.table(df)
    st.download_button("📥 엑셀 다운로드", output.getvalue(), f"{name}_진단결과.xlsx")

st.markdown("<br><hr><center>© 인천광역시교육청 학습종합클리닉센터</center>", unsafe_allow_html=True)
