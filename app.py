import os, sys, subprocess
try:
    import xlsxwriter
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "xlsxwriter"])

import streamlit as st
import pandas as pd
from datetime import datetime
import time, io

# 1. 페이지 및 세션 데이터 초기화
st.set_page_config(page_title="인천 CBT 학습진단", layout="wide")

keys = {
    'all_results': {}, 'current_q': 0, 'step': "setup", 'start_time': None,
    'sub_target': "", 'level_score': 0, 'total_read_count': 0, 'error_count': 0,
    'total_score': 0
}
for key, val in keys.items():
    if key not in st.session_state: st.session_state[key] = val

# 2. 제목 및 지필평가 안내 [cite: 754-762]
st.markdown("""
    <div style="text-align: center; background-color: #f8f9fa; padding: 20px; border-radius: 15px; border: 2px solid #0D47A1;">
        <h1 style="color: #0D47A1; margin-top: 0px;">💻 CBT 찾아가는 학습지원 진단 시스템</h1>
        <h3 style="color: #333;">인천광역시교육청 학습종합클리닉센터</h3>
        <p style="color: #d32f2f; font-weight: bold; font-size: 1.1em;">
            ※ 본 검사는 CBT뿐만 아니라 지필평가로도 실시할 수 있습니다. 각 안내된 PDF 쪽수를 활용해 주세요.
        </p>
    </div>
""", unsafe_allow_html=True)

# 3. 데이터베이스 (PDF 전수 반영)
# [기초 수학 8단계: cite 83-393]
MATH_STEPS = {
    "① 9 이하 덧셈": {"qs": ["2+1", "1+4", "1+1", "3+2", "3+1", "5+0", "1+3", "4+1", "0+3", "6+1", "1+5", "6+2", "8+1", "3+3", "4+4", "2+4", "4+3", "4+5", "3+5", "2+7", "2+6", "5+4", "1+6", "3+4", "7+1", "6+3", "5+3", "5+2", "4+2", "7+2"], "time": 60, "pass": 18, "page": "수학 23쪽"},
    "② 9 이하 뺄셈": {"qs": ["3-1", "2-1", "3-2", "5-2", "5-3", "3-3", "4-2", "5-4", "4-3", "6-1", "9-5", "8-4", "7-2", "8-5", "9-7", "8-7", "9-4", "9-2", "8-3", "7-0", "7-4", "7-5", "9-3", "7-6", "8-6", "8-1", "6-4", "8-2", "6-3", "9-6"], "time": 60, "pass": 13, "page": "수학 25쪽"},
    "③ 받아올림 덧셈": {"qs": ["9+1", "9+3", "7+3", "9+2", "8+2", "6+6", "3+8", "6+4", "2+9", "7+9", "6+8", "4+7", "6+5", "8+6", "9+4", "9+5", "4+8", "5+7", "8+9", "7+6", "4+9", "7+5", "5+9", "7+7", "9+7", "7+8", "9+9", "8+8", "5+8", "6+9"], "time": 60, "pass": 9, "page": "수학 27쪽"},
    "④ 받아내림 뺄셈": {"qs": ["10-1", "11-3", "10-5", "10-8", "12-3", "11-9", "12-4", "11-8", "11-2", "12-9", "13-6", "11-6", "13-5", "11-5", "18-9", "12-8", "15-8", "14-9", "14-7", "13-9", "13-7", "12-6", "11-7", "16-8", "12-7", "16-9", "14-8", "11-4", "15-6", "17-8"], "time": 60, "pass": 6, "page": "수학 29쪽"},
    "⑤ 몇십 몇+몇십 몇": {"qs": ["18+42", "65+88", "64+85", "31+99", "54+53", "63+70", "12+97", "41+89", "28+39", "42+76", "73+56", "18+27", "85+57", "44+49", "79+74", "93+99", "73+17", "58+99", "24+80", "68+16"], "time": 120, "pass": 7, "page": "수학 31쪽"},
    "⑥ 몇십 몇-몇십 몇": {"qs": ["47-29", "72-15", "56-27", "92-87", "60-49", "71-55", "76-68", "50-34", "52-48", "77-58", "91-53", "37-19", "45-28", "83-67", "51-39"], "time": 120, "pass": 4, "page": "수학 34쪽"},
    "⑦ 곱셈구구(1)": {"qs": [f"{a}x{b}" for a, b in [(3,1), (5,2), (2,2), (5,1), (4,2), (5,4), (2,3), (5,3), (2,4), (4,4), (3,3), (3,5), (4,5), (5,5), (2,6), (5,6), (2,7), (5,7), (2,8), (5,8), (2,9), (4,3), (3,7), (3,9), (4,8), (3,6), (4,9), (3,8), (4,6), (3,4)]], "time": 60, "pass": 16, "page": "수학 36쪽"},
    "⑧ 곱셈구구(2)": {"qs": [f"{a}x{b}" for a, b in [(6,1), (9,2), (8,2), (8,5), (9,1), (9,5), (6,5), (7,2), (7,5), (6,3), (9,4), (6,4), (7,3), (8,3), (9,3), (6,6), (8,4), (7,7), (7,4), (8,8), (9,7), (6,7), (8,9), (7,6), (6,9), (7,9), (8,6), (9,6), (6,8), (9,8)]], "time": 60, "pass": 11, "page": "수학 18쪽"}
}

# [기초 국어 10단계: cite 767, 794-803]
KOR_HANGEUL = {
    "1단계: 모음": ["ㅏ", "ㅓ", "ㅗ", "ㅜ", "ㅡ", "ㅣ", "ㅐ", "ㅔ", "ㅑ", "ㅕ"],
    "2단계: 자음": ["ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ", "ㄲ", "ㄸ", "ㅃ", "ㅆ", "ㅉ"],
    "3단계: 받침 없는 글자": ["가", "나", "다", "라", "마", "바", "사", "아", "자", "차", "카", "타", "파", "하"],
    "4단계: 받침 없는 단어": ["아파", "거미", "효자", "라디오", "배나무", "프소", "가야", "유하", "묘시", "녀타"],
    "5단계: 복잡한 모음": ["ㅘ", "ㅝ", "ㅚ", "ㅟ", "ㅢ", "ㅒ", "ㅖ", "ㅙ", "ㅞ", "ㅛ"],
    "6단계: 대표 받침": ["안", "암", "알", "압", "앗", "악", "앙"],
    "7단계: 복잡한 받침": ["밖", "있", "읽", "앉", "삶", "넓", "값"],
    "8단계: 받침 단어(의미)": ["선생님", "학교", "친구", "공부", "사랑"],
    "9단계: 받침 단어(무의미)": ["달팽미", "발차국", "준비물", "운동정", "우리너라"],
    "10단계: 듣고 쓰기": ["나무", "우유", "아이", "소", "어머니"]
}

# 4. 사이드바 및 메인 안내
with st.sidebar:
    st.header("📋 학생 정보")
    name = st.text_input("학생명 (가명)")
    grade = st.selectbox("학년", [f"초등 {i}학년" for i in range(1, 7)] + [f"중등 {i}학년" for i in range(1, 4)])
    if st.button("🔄 모든 데이터 리셋"):
        for k in st.session_state.keys(): del st.session_state[k]
        st.rerun()

if not name:
    st.warning("👈 왼쪽 사이드바에 학생 정보를 입력하세요.")
elif st.session_state.step == "setup":
    total_math_time = sum(d['time'] for d in MATH_STEPS.values()) // 60
    st.subheader(f"📍 {name} 학생 진단 센터")
    st.info(f"🔢 **기초 수학 예상 시간**: 약 {total_math_time}분 | **국어 한글 해득**: 10단계 전수 진단")
    
    c1, c2 = st.columns(2)
    if c1.button("🚀 수학 1단계부터 시작", use_container_width=True):
        st.session_state.sub_target = list(MATH_STEPS.keys())[0]
        st.session_state.step = "m_guide"; st.rerun()
    if c2.button("📖 국어 진단 메뉴 이동", use_container_width=True):
        st.session_state.step = "kor_menu"; st.rerun()

    # 통합 엑셀 다운로드 (데이터가 있을 때만 표시)
    if st.session_state.all_results:
        st.divider()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for sheet, data in st.session_state.all_results.items():
                pd.DataFrame(data).to_excel(writer, sheet_name=sheet[:31], index=False)
        st.download_button("📥 모든 결과 통합 엑셀 다운로드", output.getvalue(), f"{name}_전체결과.xlsx")

# --- 수학 8단계 로직 (타이머 및 판정 포함) --- [cite: 13, 48-66, 75-76]
elif st.session_state.step == "m_guide":
    target = st.session_state.sub_target
    data = MATH_STEPS[target]
    st.subheader(f"📝 {target} 안내")
    st.warning(f"선생님의 '시작' 신호와 함께 {data['time']//60}분간 진행합니다. '그만' 소리에 즉시 멈춥니다.")
    st.markdown(f"**📄 지필평가 병행 시:** 검사지 **{data['page']}**를 펼쳐주세요.")
    if st.button("CBT 타이머 시작"):
        st.session_state.update({'step': "m_test", 'start_time': time.time(), 'current_q': 0, 'total_score': 0})
        if target not in st.session_state.all_results: st.session_state.all_results[target] = []
        st.rerun()

elif st.session_state.step == "m_test":
    target = st.session_state.sub_target
    data = MATH_STEPS[target]
    rem = max(0, data['time'] - int(time.time() - st.session_state.start_time))
    
    st.progress(rem / data['time'])
    st.markdown(f"<h2 style='text-align: center; color: red;'>남은 시간: {rem}초</h2>", unsafe_allow_html=True)
    
    if rem <= 0 or st.session_state.current_q >= len(data['qs']):
        st.error("⏳ 시간 종료! 교사: \"그만!\" 학생은 연필을 내려놓으세요.")
        if st.button("결과 확인"): st.session_state.step = "m_res"; st.rerun()
    else:
        q = data['qs'][st.session_state.current_q]
        st.markdown(f"<h1 style='text-align: center; font-size: 150px;'>{q}</h1>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        if c1.button("⭕ 정답", use_container_width=True):
            st.session_state.all_results[target].append({"문항": q, "결과": "정답", "점수": 1})
            st.session_state.total_score += 1; st.session_state.current_q += 1; st.rerun()
        if c2.button("❌ 오답", use_container_width=True):
            st.session_state.all_results[target].append({"문항": q, "결과": "오답", "점수": 0})
            st.session_state.current_q += 1; st.rerun()
    time.sleep(0.5); st.rerun()

elif st.session_state.step == "m_res":
    target = st.session_state.sub_target
    score = st.session_state.total_score
    pass_mark = MATH_STEPS[target]['pass']
    st.subheader(f"📊 {target} 판정 결과")
    
    if score >= pass_mark:
        st.success(f"✅ **도달** (취득 {score}점 / 기준 {pass_mark}점)")
        steps = list(MATH_STEPS.keys()); curr_idx = steps.index(target)
        if curr_idx + 1 < len(steps) and st.button(f"➡️ 다음 단계({steps[curr_idx+1]}) 진행"):
            st.session_state.sub_target = steps[curr_idx+1]; st.session_state.step = "m_guide"; st.rerun()
    else:
        st.error(f"❌ **미도달** (취득 {score}점 / 기준 {pass_mark}점)")
        st.warning(f"💡 **출발점 발견:** 아동은 이 단계의 기초선 보충 지도가 필요합니다.")
    
    if st.button("🏠 메인으로 돌아가기"): st.session_state.step = "setup"; st.rerun()

# --- 국어 10단계 실행 로직 (전 문항 반영) --- [cite: 767, 794-803]
elif st.session_state.step == "kor_menu":
    st.subheader("📖 국어 한글 해득 단계 선택")
    for level in KOR_HANGEUL.keys():
        if st.button(level, use_container_width=True):
            st.session_state.sub_target = level; st.session_state.step = "k_run"; st.session_state.current_q = 0
            if level not in st.session_state.all_results: st.session_state.all_results[level] = []
            st.rerun()
    if st.button("🏠 이전으로"): st.session_state.step = "setup"; st.rerun()

elif st.session_state.step == "k_run":
    level = st.session_state.sub_target
    qs = KOR_HANGEUL[level]
    q = qs[st.session_state.current_q]
    st.markdown(f"<h1 style='text-align: center; font-size: 150px;'>{q}</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    if c1.button("⭕ 정답"):
        st.session_state.all_results[level].append({"문항": q, "점수": 1})
        st.session_state.current_q += 1
        if st.session_state.current_q >= len(qs): st.session_state.step = "setup"
        st.rerun()
    if c2.button("❌ 오답"):
        st.session_state.all_results[level].append({"문항": q, "점수": 0})
        st.session_state.current_q += 1
        if st.session_state.current_q >= len(qs): st.session_state.step = "setup"
        st.rerun()

st.markdown("<br><hr><center>© 인천광역시교육청 CBT 학습종합클리닉센터</center>", unsafe_allow_html=True)
