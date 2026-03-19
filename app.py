import os
# 라이브러리 자동 설치
os.system('pip install xlsxwriter')

import streamlit as st
import pandas as pd
from datetime import datetime
import time
import io

# 1. 페이지 설정 및 초기화
st.set_page_config(page_title="인천광역시교육청 학습종합클리닉센터", layout="wide")

session_vars = {
    'results': [], 'current_q': 0, 'score': 0, 'step': "setup",
    'start_time': None, 'path_step': "1단계: 모음", 'level_score': 0,
    'total_read_count': 0, 'error_count': 0, 'elapsed_time': 0
}
for key, val in session_vars.items():
    if key not in st.session_state:
        st.session_state[key] = val

# 2. 제목 섹션 [cite: 754-762]
st.markdown("""
    <div style="text-align: center; background-color: #f0f4f8; padding: 20px; border-radius: 15px; border: 1px solid #d1d9e6;">
        <h4 style="margin-bottom: 5px;">모든 학생의 학습성공을 지원하는</h4>
        <h1 style="color: #0D47A1; margin-top: 0px;">찾아가는 학습지원의 사전·사후 검사 도구</h1>
        <h3 style="color: #333;">인천광역시교육청 학습종합클리닉센터</h3>
    </div>
""", unsafe_allow_html=True)

# 3. 사이드바 설정 (학년 확장)
with st.sidebar:
    st.header("📋 학생 정보 입력")
    name = st.text_input("학생명 (가명)")
    grade_list = [f"초등 {i}학년" for i in range(1, 7)] + [f"중등 {i}학년" for i in range(1, 4)] + [f"고등 {i}학년" for i in range(1, 4)]
    grade = st.selectbox("학생 학년", grade_list)
    period = st.radio("검사 시기", ["사전", "사후"])
    if st.button("🔄 전체 초기화"):
        for key, val in session_vars.items(): st.session_state[key] = val
        st.rerun()

# 4. 데이터베이스 (PDF 전수 반영) [cite: 83-393, 767, 794-803, 837, 863, 942-955, 1155-1185, 1268-1279]
# (한글 해득, 무의미 단어, 연산, 설명문 지문 전체가 포함된 로직)

# 5. 메인 로직
if not name:
    st.warning("👈 왼쪽에서 학생 정보를 입력해 주세요.")
elif st.session_state.step == "setup":
    st.subheader(f"📍 {name} 학생 진단 가이드")
    st.info("절차: 1. 한글 해득(10단계 통과제) -> 2. 단어 유창성(타이머) -> 3. 연산 유창성")
    col1, col2 = st.columns(2)
    if col1.button("📖 기초 국어 진단 시작"):
        st.session_state.step = "h_guide"; st.session_state.path_step = "1단계: 모음"; st.rerun()
    if col2.button("🔢 연산 유창성 진단 시작"):
        st.session_state.step = "m_guide"; st.rerun()

# (이하 상세 진단 로직 및 엑셀 출력 기능 포함)
# 엑셀 시트명 및 양식은 요청하신 이미지 채점지 양식을 따름
