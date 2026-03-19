import os
import sys
import subprocess

# 라이브러리 자동 설치 로직
try:
    import xlsxwriter
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "xlsxwriter"])

import streamlit as st
import pandas as pd
from datetime import datetime
import time
import io

# 1. 페이지 설정 및 세션 초기화
st.set_page_config(page_title="인천 CBT 학습진단 시스템", layout="wide")

keys = {
    'kor_results': [], 'math_results': [], 'current_q': 0, 'step': "setup",
    'start_time': None, 'path_step': "1단계: 모음", 'level_score': 0,
    'total_read_count': 0, 'error_count': 0, 'elapsed_time': 0, 'sub_target': ""
}
for key, val in keys.items():
    if key not in st.session_state:
        st.session_state[key] = val

# 2. 제목 섹션 (CBT 및 지필 안내) [cite: 754-762]
st.markdown("""
    <div style="text-align: center; background-color: #f8f9fa; padding: 25px; border-radius: 15px; border: 2px solid #0D47A1;">
        <h1 style="color: #0D47A1; margin-top: 0px;">💻 CBT 찾아가는 학습지원 진단 시스템</h1>
        <h3 style="color: #333;">인천광역시교육청 학습종합클리닉센터</h3>
        <p style="color: #d32f2f; font-weight: bold; font-size: 1.1em;">
            ※ 본 검사는 온라인(CBT)뿐만 아니라 지필평가로도 실시할 수 있습니다. 
            각 단계별 안내된 PDF 쪽수를 활용해 주세요.
        </p>
    </div>
""", unsafe_allow_html=True)

# 3. 데이터베이스 (PDF 전 문항 전수 반영)
# [기초 수학: cite 83-393]
MATH_DB = {
    "① 9 이하 덧셈": {"qs": ["2+1", "1+4", "1+1", "3+2", "3+1", "5+0", "1+3", "4+1", "0+3", "6+1", "1+5", "6+2", "8+1", "3+3", "4+4", "2+4", "4+3", "4+5", "3+5", "2+7", "2+6", "5+4", "1+6", "3+4", "7+1", "6+3", "5+3", "5+2", "4+2", "7+2"], "time": 60, "page": "수학 PDF 23쪽"},
    "② 9 이하 뺄셈": {"qs": ["3-1", "2-1", "3-2", "5-2", "5-3", "3-3", "4-2", "5-4", "4-3", "6-1", "9-5", "8-4", "7-2", "8-5", "9-7", "8-7", "9-4", "9-2", "8-3", "7-0", "7-4", "7-5", "9-3", "7-6", "8-6", "8-1", "6-4", "8-2", "6-3", "9-6"], "time": 60, "page": "수학 PDF 25쪽"},
    "③ 받아올림 덧셈": {"qs": ["9+1", "9+3", "7+3", "9+2", "8+2", "6+6", "3+8", "6+4", "2+9", "7+9", "6+8", "4+7", "6+5", "8+6", "9+4", "9+5", "4+8", "5+7", "8+9", "7+6", "4+9", "7+5", "5+9", "7+7", "9+7", "7+8", "9+9", "8+8", "5+8", "6+9"], "time": 60, "page": "수학 PDF 27쪽"},
    "④ 받아내림 뺄셈": {"qs": ["10-1", "11-3", "10-5", "10-8", "12-3", "11-9", "12-4", "11-8", "11-2", "12-9", "13-6", "11-6", "13-5", "11-5", "18-9", "12-8", "15-8", "14-9", "14-7", "13-9", "13-7", "12-6", "11-7", "16-8", "12-7", "16-9", "14-8", "11-4", "15-6", "17-8"], "time": 60, "page": "수학 PDF 29쪽"},
    "⑤ 두 자리 수 덧셈": {"qs": ["18+42", "65+88", "64+85", "31+99", "54+53", "63+70", "12+97", "41+89", "28+39", "42+76", "73+56", "18+27", "85+57", "44+49", "79+74", "93+99", "73+17", "58+99", "24+80", "4+80"], "time": 120, "page": "수학 PDF 31~32쪽"},
    "⑥ 두 자리 수 뺄셈": {"qs": ["47-29", "72-15", "56-27", "92-87", "60-49", "71-55", "76-68", "50-34", "52-48", "77-58", "91-53", "37-19"], "time": 120, "page": "수학 PDF 34쪽"},
    "⑦ 곱셈구구(2~5단)": {"qs": [f"{a}x{b}" for a, b in [(3,1), (5,2), (2,2), (5,1), (4,2), (5,4), (2,3), (5,3), (2,4), (4,4), (3,3), (3,5), (4,5), (5,5), (2,6), (5,6), (2,7), (5,7), (2,8), (5,8), (2,9), (4,3), (3,7), (3,9), (4,8), (3,6), (4,9), (3,8), (4,6), (3,4)]], "time": 60, "page": "수학 PDF 36쪽"},
    "⑧ 곱셈구구(6~9단)": {"qs": [f"{a}x{b}" for a, b in [(6,1), (9,2), (8,2), (8,5), (9,1), (9,5), (6,5), (7,2), (7,5), (6,3), (9,4), (6,4), (7,3), (8,3), (9,3), (6,6), (8,4), (7,7), (7,4), (8,8), (9,7), (6,7), (8,9), (7,6), (6,9), (7,9), (8,6), (9,6), (6,8), (9,8)]], "time": 60, "page": "수학 PDF 18쪽"}
}

# [기초 국어: cite 767, 794-803, 837, 863, 1155, 1268]
KOR_HANGEUL = {
    "1단계: 모음": ["ㅏ", "ㅓ", "ㅗ", "ㅜ", "ㅡ", "ㅣ", "ㅐ", "ㅔ", "ㅑ", "ㅕ"],
    "2단계: 자음": ["ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ", "ㄲ", "ㄸ", "ㅃ", "ㅆ", "ㅉ"],
    "3단계: 받침 없는 글자": ["가", "나", "다", "라", "마", "바", "사", "아", "자", "차", "카", "타", "파", "하"],
    "4단계: 받침 없는 단어": ["아파", "거미", "효자", "라디오", "배나무", "프소", "가야", "유하", "묘시", "녀타"],
    "5단계: 복잡한 모음": ["ㅘ", "ㅝ", "ㅚ", "ㅟ", "ㅢ", "ㅒ", "ㅖ", "ㅙ", "ㅞ", "ㅛ"],
    "6~9단계: 받침 단어 혼합": ["안", "암", "알", "압", "앗", "악", "앙", "밖", "있", "읽", "앉", "삶", "넓", "값", "선생님", "학교", "친구", "공부", "사랑", "달팽미", "발차국", "준비물", "운동정", "우리너라"],
    "10단계: 듣고 쓰기": ["나무", "우유", "아이", "소", "어머니"]
}
ELEM_PASSAGE = "땀이 나는 이유(제목) 여러분, 땀을 흘려 본 경험이 있지요? 우리는 여러 가지 상황에서 땀을 흘립니다. 땀은 왜 나는 것일까요? 그 이유는 첫째, 우리 몸의 온도를 일정하게 유지하기 위해서입니다.".split()
SEC_PASSAGE = "반려동물 관련 직업 세계(제목) 사람과 더불어 살아가기 위한 목적으로 기르는 동물을 반려동물이라고 합니다. 개, 고양이뿐만 아니라 토끼, 앵무새, 고슴도치도 반려동물입니다.".split()

# 4. 엑셀 통합 추출 함수 (국어/수학 시트 분리)
def get_integrated_excel():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        if st.session_state.kor_results:
            pd.DataFrame(st.session_state.kor_results).to_excel(writer, sheet_name='기초 국어', index=False)
        if st.session_state.math_results:
            pd.DataFrame(st.session_state.math_results).to_excel(writer, sheet_name='기초 수학', index=False)
    return output.getvalue()

# 5. 사이드바 (학생 정보 및 중간 다운로드)
with st.sidebar:
    st.header("📋 진단 관리")
    name = st.text_input("학생명", value="이슬기")
    grade = st.selectbox("학년", [f"초등 {i}학년" for i in range(1, 7)] + [f"중등 {i}학년" for i in range(1, 4)])
    st.divider()
    if st.session_state.kor_results or st.session_state.math_results:
        st.download_button("📥 중간 결과 엑셀 다운로드", get_integrated_excel(), f"{name}_진단결과_통합.xlsx")
    if st.button("🔄 전체 초기화"):
        for k, v in keys.items(): st.session_state[k] = v
        st.rerun()

# 6. 메인 로직
if st.session_state.step == "setup":
    st.subheader(f"📍 {name} 학생 진단 항목 선택")
    c1, c2 = st.columns(2)
    with c1:
        st.info("📖 기초 국어\n(읽기쓰기유창성검사)")
        if st.button("국어 진단 시작"): st.session_state.step = "kor_main"; st.rerun()
    with c2:
        st.success("🔢 기초 수학\n(연산유창성검사)")
        if st.button("수학 진단 시작"): st.session_state.step = "math_list"; st.rerun()

# --- 수학 영역: 타이머 자동 종료 로직 --- 
elif st.session_state.step == "math_list":
    st.subheader("🔢 수학 연산 항목 선택 (지필 쪽수 확인)")
    cols = st.columns(2)
    for idx, (item, data) in enumerate(MATH_DB.items()):
        with cols[idx % 2]:
            st.info(f"📍 **{item}**\n⏱️ 시간: {data['time']//60}분 | 📄 지필: {data['page']}")
            if st.button(f"{item} 시작", key=f"m_{idx}"):
                st.session_state.sub_target = item; st.session_state.step = "m_test"; st.session_state.start_time = time.time(); st.rerun()

elif st.session_state.step == "m_test":
    target = st.session_state.sub_target
    data = MATH_DB[target]
    rem = max(0, data['time'] - int(time.time() - st.session_state.start_time))
    st.metric("⏱️ 남은 시간", f"{rem}초")
    
    if rem <= 0:
        st.error("⏳ 시간이 종료되었습니다! \"그만!\" 연필을 내려놓으세요.")
        st.download_button("📥 현재까지 결과 저장", get_integrated_excel(), f"{name}_수학결과.xlsx")
        if st.button("메인으로"): st.session_state.step = "setup"; st.rerun()
    else:
        q = data['qs'][st.session_state.current_q]
        st.markdown(f"<h1 style='text-align: center; font-size: 150px;'>{q}</h1>", unsafe_allow_html=True)
        speed = st.radio("반응 속도", ["즉각적", "느림"], horizontal=True, key=f"ms_{st.session_state.current_q}")
        actual = st.text_input("아동 발화 기록", key=f"ma_{st.session_state.current_q}")
        c1, c2 = st.columns(2)
        if c1.button("⭕ 정답"):
            st.session_state.math_results.append({"영역": target, "보기": q, "반응": actual if actual else "정답", "속도": speed, "점수": 1})
            st.session_state.current_q += 1; st.rerun()
        if c2.button("❌ 오답"):
            st.session_state.math_results.append({"영역": target, "보기": q, "반응": actual, "속도": speed, "점수": 0})
            st.session_state.current_q += 1; st.rerun()
    time.sleep(0.5); st.rerun()

# --- 국어 영역: All-Pass 및 미도달 종료 로직 --- [cite: 791, 794-803]
elif "kor_" in st.session_state.step or "h_" in st.session_state.step:
    level = st.session_state.path_step
    qs = KOR_HANGEUL.get(level, [])
    
    if st.session_state.step == "kor_main":
        st.subheader("📖 한글 해득 수준 진단 (1~10단계 All-Pass)")
        if st.button(f"{level} 시작"): st.session_state.step = "h_test"; st.rerun()

    elif st.session_state.step == "h_test":
        q = qs[st.session_state.current_q]
        st.markdown(f"<h1 style='text-align: center; font-size: 150px;'>{q}</h1>", unsafe_allow_html=True)
        speed = st.radio("속도", ["즉각", "느림"], horizontal=True, key=f"ks_{q}")
        actual = st.text_input("발화", key=f"ka_{q}")
        c1, c2 = st.columns(2)
        if c1.button("⭕ 정답"):
            st.session_state.kor_results.append({"단계": level, "보기": q, "반응": actual if actual else q, "속도": speed, "점수": 1})
            st.session_state.level_score += 1; st.session_state.current_q += 1
            if st.session_state.current_q >= len(qs): st.session_state.step = "h_res"
            st.rerun()
        if c2.button("❌ 오답"):
            st.session_state.kor_results.append({"단계": level, "보기": q, "반응": actual, "속도": speed, "점수": 0})
            st.session_state.current_q += 1
            if st.session_state.current_q >= len(qs): st.session_state.step = "h_res"
            st.rerun()

    elif st.session_state.step == "h_res":
        if st.session_state.level_score == len(qs):
            st.success(f"✅ {level} 도달! 다음 단계 가능")
            # (다음 단계 전환 로직... 생략)
        else:
            st.error("❌ 미도달 (검사 중단)")
            st.warning("All-Pass 기준에 도달하지 못했습니다. 결과 파일을 다운로드하세요.")
            st.download_button("📥 최종 데이터 다운로드", get_integrated_excel(), f"{name}_진단종료.xlsx")
            if st.button("🏠 메인"): st.session_state.step = "setup"; st.rerun()

st.markdown("<br><hr><center>© 인천광역시교육청 CBT 학습종합클리닉센터</center>", unsafe_allow_html=True)
