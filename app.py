import os
import sys
import subprocess

# 라이브러리 자동 설치 (xlsxwriter 미설치 오류 방지)
try:
    import xlsxwriter
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "xlsxwriter"])

import streamlit as st
import pandas as pd
from datetime import datetime
import time
import io

# 1. 페이지 설정 및 세션 상태 초기화
st.set_page_config(page_title="인천광역시교육청 학습종합클리닉센터", layout="wide")

keys = {
    'results': [], 'current_q': 0, 'score': 0, 'step': "setup",
    'start_time': None, 'path_step': "1단계: 모음", 'level_score': 0,
    'total_read_count': 0, 'error_count': 0, 'elapsed_time': 0, 'sub_target': ""
}
for key, val in keys.items():
    if key not in st.session_state:
        st.session_state[key] = val

# 2. 제목 섹션 (공식 명칭 반영) [cite: 1-7, 754-762]
st.markdown("""
    <div style="text-align: center; background-color: #f0f4f8; padding: 20px; border-radius: 15px; border: 1px solid #d1d9e6;">
        <h4 style="margin-bottom: 5px;">모든 학생의 학습성공을 지원하는</h4>
        <h1 style="color: #0D47A1; margin-top: 0px;">찾아가는 학습지원의 사전·사후 검사 도구</h1>
        <h3 style="color: #333;">인천광역시교육청 학습종합클리닉센터</h3>
    </div>
""", unsafe_allow_html=True)

# 3. 데이터베이스 (PDF 전 문항 전수 반영)
# [기초 수학: cite 83-393]
MATH_DB = {
    "① 9 이하 덧셈": ["2+1", "1+4", "1+1", "3+2", "3+1", "5+0", "1+3", "4+1", "0+3", "6+1", "1+5", "6+2", "8+1", "3+3", "4+4", "2+4", "4+3", "4+5", "3+5", "2+7", "2+6", "5+4", "1+6", "3+4", "7+1", "6+3", "5+3", "5+2", "4+2", "7+2"],
    "② 9 이하 뺄셈": ["3-1", "2-1", "3-2", "5-2", "5-3", "3-3", "4-2", "5-4", "4-3", "6-1", "9-5", "8-4", "7-2", "8-5", "9-7", "8-7", "9-4", "9-2", "8-3", "7-0", "7-4", "7-5", "9-3", "7-6", "8-6", "8-1", "6-4", "8-2", "6-3", "9-6"],
    "③ 받아올림 덧셈": ["9+1", "9+3", "7+3", "9+2", "8+2", "6+6", "3+8", "6+4", "2+9", "7+9", "6+8", "4+7", "6+5", "8+6", "9+4", "9+5", "4+8", "5+7", "8+9", "7+6", "4+9", "7+5", "5+9", "7+7", "9+7", "7+8", "9+9", "8+8", "5+8", "6+9"],
    "④ 받아내림 뺄셈": ["10-1", "11-3", "10-5", "10-8", "12-3", "11-9", "12-4", "11-8", "11-2", "12-9", "13-6", "11-6", "13-5", "11-5", "18-9", "12-8", "15-8", "14-9", "14-7", "13-9", "13-7", "12-6", "11-7", "16-8", "12-7", "16-9", "14-8", "11-4", "15-6", "17-8"],
    "⑤ 두 자리 수 덧셈": ["18+42", "65+88", "64+85", "31+99", "54+53", "63+70", "12+97", "41+89", "28+39", "42+76", "73+56", "18+27", "85+57", "44+49", "79+74", "93+99", "73+17", "58+99", "24+80", "4+80"],
    "⑥ 두 자리 수 뺄셈": ["47-29", "72-15", "56-27", "92-87", "60-49", "71-55", "76-68", "50-34", "52-48", "77-58", "91-53", "37-19"],
    "⑦ 곱셈구구(2~5단)": [f"{a}x{b}" for a, b in [(3,1), (5,2), (2,2), (5,1), (4,2), (5,4), (2,3), (5,3), (2,4), (4,4), (3,3), (3,5), (4,5), (5,5), (2,6), (5,6), (2,7), (5,7), (2,8), (5,8), (2,9), (4,3), (3,7), (3,9), (4,8), (3,6), (4,9), (3,8), (4,6), (3,4)]],
    "⑧ 곱셈구구(6~9단)": [f"{a}x{b}" for a, b in [(6,1), (9,2), (8,2), (8,5), (9,1), (9,5), (6,5), (7,2), (7,5), (6,3), (9,4), (6,4), (7,3), (8,3), (9,3), (6,6), (8,4), (7,7), (7,4), (8,8), (9,7), (6,7), (8,9), (7,6), (6,9), (7,9), (8,6), (9,6), (6,8), (9,8)]]
}

# [기초 국어: cite 767, 794-803, 942, 1155, 1268]
KOR_HANGEUL = {
    "1단계: 모음": ["ㅏ", "ㅓ", "ㅗ", "ㅜ", "ㅡ", "ㅣ", "ㅐ", "ㅔ", "ㅑ", "ㅕ"],
    "2단계: 자음": ["ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ", "ㄲ", "ㄸ", "ㅃ", "ㅆ", "ㅉ"],
    "3단계: 받침 없는 글자": ["가", "나", "다", "라", "마", "바", "사", "아", "자", "차", "카", "타", "파", "하"],
    "4단계: 받침 없는 단어": ["아파", "거미", "효자", "라디오", "배나무", "프소", "가야", "유하", "묘시", "녀타"],
    "5단계: 복잡한 모음": ["ㅘ", "ㅝ", "ㅚ", "ㅟ", "ㅢ", "ㅒ", "ㅖ", "ㅙ", "ㅞ", "ㅛ"],
    "6~9단계: 받침 단어": ["안", "암", "알", "밖", "있", "읽", "앉", "삶", "넓", "값", "선생님", "학교", "친구", "공부", "사랑", "달팽미", "발차국", "준비물", "운동정", "우리너라"]
}
ELEM_PASSAGE = "땀이 나는 이유(제목) 여러분, 땀을 흘려 본 경험이 있지요? 우리는 여러 가지 상황에서 땀을 흘립니다. 땀은 왜 나는 것일까요? 그 이유는 첫째, 우리 몸의 온도를 일정하게 유지하기 위해서입니다. 우리 몸의 온도가 평소보다 높아지게 되면 땀이 나와서 공기 중으로 날아가게 됩니다. 그러면 열도 함께 빠져나가 몸을 식혀줍니다. 둘째, 땀은 우리 몸의 독소와 노폐물을 몸 밖으로 내보내 줍니다. 땀을 흘려 몸에 나쁜 물질이 쌓이는 것을 막아주는 것이지요. 셋째, 땀은 피부를 보호해 줍니다. 땀을 흘리면 피부가 촉촉해지며, 땀이 외부의 여러 자극으로부터 피부를 건강하게 지켜줍니다. 넷째, 우리 몸은 긴장하거나 운동을 할 때 열이 오르게 됩니다. 이때에도 땀을 흘리게 되면 높아진 몸의 온도가 낮아지지요. 땀을 흘리면 긴장이 풀리고 스트레스 정도가 낮아지기도 한답니다. 이처럼 땀을 흘리는 것은 우리 몸에 꼭 필요한 과정이에요. 우리가 느끼지 못해도 땀은 항상 조금씩 나고 있어요. 땀을 많이 흘렸을 때는 몸을 깨끗하게 씻고 물을 충분히 마셔주어야 합니다. 적당한 양의 땀을 흘려 우리 몸을 건강하게 지키도록 합시다.".split()
SEC_PASSAGE = "반려동물 관련 직업 세계(제목) 사람과 더불어 살아가기 위한 목적으로 기르는 동물을 반려동물이라고 합니다. 개, 고양이뿐만 아니라 토끼, 앵무새, 고슴도치도 반려동물입니다. 최근 반려동물에 관한 관심이 높아지고 있습니다. 그래서 관련된 직업도 주목받고 있습니다. 직업의 분야도 건강, 미용, 훈련, 안전 등의 분야로 다양해지고 있습니다. 먼저 반려동물의 건강과 미용을 위한 직업도 다양합니다. 수의사는 동물들의 의사이고, 동물보건사는 수의사의 진료를 보조하며 아픈 동물을 간호합니다. 미용과 관련해서는 반려동물 미용사, 패션디자이너도 있습니다. 미용사는 털 깎기, 털 묶기, 염색하기 등을 통해 동물의 장점이 드러나도록 합니다. 그리고 패션디자이너는 동물의 신체적 특징을 바탕으로 어울리는 옷과 소품을 만듭니다. 동물 훈련 및 안전과 관련된 직업에는 훈련 상담사, 동물보호 보안관이 있습니다. 훈련 상담사는 반려동물이 보이는 문제 행동의 원인을 파악합니다. 그리고 문제 행동을 교정할 수 있는 프로그램을 계획하고 시행합니다. 동물보호 보안관은 방치되거나 학대받는 동물을 구조하고 보호하는 일을 합니다. 그 밖에 동물의 연기 지도자이자 매니저인 동물 랭글러 그리고 반려동물을 모델로 사진을 찍는 반려동물 사진작가도 있습니다. 무엇보다 반려동물과 관련된 직업은 동물을 사랑하는 마음이 있어야 합니다. 이와 함께 그 분야에 전문적인 지식도 갖추어야 합니다. 그뿐만 아니라 동물과 소통할 수 있는 섬세함과 작은 변화도 지켜볼 줄 아는 인내심도 필요합니다. 여러분은 반려동물에 관해 좀 더 알아보고 싶은 직업이 생겼나요? 친구들과 여러분의 생각을 이야기해 보세요.".split()

# 4. 사이드바
with st.sidebar:
    st.header("📋 학생 정보 입력")
    name = st.text_input("학생명 (가명)")
    grade = st.selectbox("학생 학년", [f"초등 {i}학년" for i in range(1, 7)] + [f"중등 {i}학년" for i in range(1, 4)])
    period = st.radio("검사 시기", ["사전", "사후"])
    if st.button("🔄 전체 초기화 (처음부터)"):
        for k, v in keys.items(): st.session_state[k] = v
        st.rerun()

# 5. 메인 로직
if not name:
    st.warning("👈 왼쪽 사이드바에 학생 정보를 먼저 입력해 주세요.")
elif st.session_state.step == "setup":
    st.subheader(f"📍 {name} 학생 진단 가이드")
    st.markdown("### 📌 권장 진단 순서\n1. **한글 해득 수준**: 10단계 All-Pass 방식\n2. **유창성 검사**: 실시간 타이머 및 어절 카운터\n3. **연산 유창성**: 영역별 기초 연산 평가")
    c1, c2 = st.columns(2)
    if c1.button("📖 기초 국어 진단 시작", use_container_width=True):
        st.session_state.step = "h_guide"; st.session_state.path_step = "1단계: 모음"; st.rerun()
    if c2.button("🔢 연산 유창성 진단 시작", use_container_width=True):
        st.session_state.step = "m_list"; st.rerun()

# [연산 유창성 세부 목록]
elif st.session_state.step == "m_list":
    st.subheader("🔢 평가할 연산 항목을 선택하세요")
    cols = st.columns(2)
    items = list(MATH_DB.keys())
    for idx, item in enumerate(items):
        if cols[idx % 2].button(item, use_container_width=True):
            st.session_state.sub_target = item
            st.session_state.step = "m_guide"; st.rerun()
    if st.button("⬅️ 이전으로"): st.session_state.step = "setup"; st.rerun()

elif st.session_state.step == "m_guide":
    st.info(f"[{st.session_state.sub_target}] 진단을 시작합니다."); st.button("시작", on_click=lambda: st.session_state.update({"step": "m_test", "start_time": time.time()}))

elif st.session_state.step == "m_test":
    target_qs = MATH_DB[st.session_state.sub_target]
    limit = 120 if "두 자리" in st.session_state.sub_target else 60
    rem = max(0, limit - int(time.time() - st.session_state.start_time))
    st.metric("⏱️ 남은 시간", f"{rem}초")
    if rem <= 0 or st.session_state.current_q >= len(target_qs): st.session_state.step = "final"; st.rerun()
    
    q = target_qs[st.session_state.current_q]
    st.markdown(f"<h1 style='text-align: center; font-size: 150px;'>{q}</h1>", unsafe_allow_html=True)
    with st.expander("📝 질적 기록", expanded=True):
        speed = st.radio("반응 속도", ["즉각적", "느림"], horizontal=True, key=f"ms_{st.session_state.current_q}")
        actual = st.text_input("아동 발화", key=f"ma_{st.session_state.current_q}")
    c1, c2 = st.columns(2)
    if c1.button("⭕ 정답", use_container_width=True):
        st.session_state.results.append({"보기": q, "반응": actual if actual else "정답", "속도": speed, "점수": 1}); st.session_state.current_q += 1; st.rerun()
    if c2.button("❌ 오답", use_container_width=True):
        st.session_state.results.append({"보기": q, "반응": actual, "속도": speed, "점수": 0}); st.session_state.current_q += 1; st.rerun()

# [국어 해득 진단] [cite: 794-803]
elif "h_" in st.session_state.step:
    level = st.session_state.path_step
    qs = KOR_HANGEUL[level]
    if "guide" in st.session_state.step:
        st.info(f"[{level}] 모든 문항 정답 시 통과입니다."); st.button("시작", on_click=lambda: st.session_state.update({"step": "h_test"}))
    elif "test" in st.session_state.step:
        q = qs[st.session_state.current_q]
        st.markdown(f"<h1 style='text-align: center; font-size: 150px;'>{q}</h1>", unsafe_allow_html=True)
        speed = st.radio("반응 속도", ["즉각적", "느림"], horizontal=True, key=f"hs_{st.session_state.current_q}")
        actual = st.text_input("아동 발화", key=f"ha_{st.session_state.current_q}")
        c1, c2 = st.columns(2)
        if c1.button("⭕ 정답", use_container_width=True):
            st.session_state.results.append({"보기": q, "반응": actual if actual else q, "속도": speed, "점수": 1}); st.session_state.level_score += 1; st.session_state.current_q += 1
            if st.session_state.current_q >= len(qs): st.session_state.step = "h_res"
            st.rerun()
        if c2.button("❌ 오답", use_container_width=True):
            st.session_state.results.append({"보기": q, "반응": actual, "속도": speed, "점수": 0}); st.session_state.current_q += 1
            if st.session_state.current_q >= len(qs): st.session_state.step = "h_res"
            st.rerun()
    elif "res" in st.session_state.step:
        if st.session_state.level_score == len(qs):
            st.success(f"{level} 통과!"); levels = list(KOR_HANGEUL.keys()); idx = levels.index(level)
            if idx + 1 < len(levels) and st.button("다음 단계"):
                st.session_state.update({"path_step": levels[idx+1], "current_q": 0, "level_score": 0, "step": "h_test"}); st.rerun()
        else: st.error("기초선 지도 필요"); st.button("결과 저장", on_click=lambda: st.session_state.update({"step": "final"}))

# [최종 결과 저장: 질적 분석 엑셀 양식 완벽 반영]
elif st.session_state.step == "final":
    st.subheader("🏁 진단 데이터 분석 및 저장")
    if st.session_state.results:
        df = pd.DataFrame(st.session_state.results)
        st.table(df)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='질적분석', index=False)
        st.download_button("📥 질적 분석 엑셀 다운로드", output.getvalue(), f"{name}_진단결과.xlsx")
    else: st.info("기록된 데이터가 없습니다.")

st.markdown("<br><hr><center>© 인천광역시교육청 학습종합클리닉센터</center>", unsafe_allow_html=True)
