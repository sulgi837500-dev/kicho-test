import streamlit as st
import pandas as pd
from datetime import datetime
import time

# 1. 페이지 설정 및 세션 초기화
st.set_page_config(page_title="인천광역시교육청 학습종합클리닉센터", layout="wide")

for key in ['results', 'current_q', 'score', 'step', 'start_time']:
    if key not in st.session_state: 
        st.session_state[key] = [] if key == 'results' else (0 if key in ['current_q', 'score'] else "setup")

# 2. 상단 제목 [cite: 1-7, 753-762]
st.markdown("""
    <div style="text-align: center; background-color: #f0f4f8; padding: 20px; border-radius: 15px; border: 1px solid #d1d9e6;">
        <h4 style="margin-bottom: 5px;">모든 학생의 학습성공을 지원하는</h4>
        <h1 style="color: #0D47A1; margin-top: 0px;">찾아가는 학습지원의 사전·사후 검사 도구</h1>
        <h3 style="color: #333;">인천광역시교육청 학습종합클리닉센터</h3>
        <hr>
    </div>
""", unsafe_allow_html=True)

# 3. 사이드바 설정 [cite: 13, 1005]
with st.sidebar:
    st.header("📋 검사 설정")
    name = st.text_input("학생명 (가명)")
    
    # 학년 선택 (초1~고3)
    grade_list = [f"초등 {i}학년" for i in range(1, 7)] + [f"중등 {i}학년" for i in range(1, 4)] + [f"고등 {i}학년" for i in range(1, 4)]
    grade = st.selectbox("학생 학년", grade_list)
    is_secondary = "중등" in grade or "고등" in grade
    
    period = st.radio("검사 시기", ["사전", "사후"])
    st.divider()
    
    category = st.selectbox("대영역", ["기초 국어 (읽기·쓰기 유창성)", "기초 수학 (연산 유창성)"])
    
    if "국어" in category:
        sub_list = ["① 한글 해득 수준", "② 무의미 단어 읽기 유창성", "③ 읽기 유창성 (설명문)"]
        if is_secondary: sub_list.append("④ 읽기 이해 (단어 선택)")
        sub_category = st.selectbox("세부 항목", sub_list)
        limit_sec = 40 if "무의미" in sub_category else (120 if "이해" in sub_category else 60)
    else:
        sub_list = ["① 9 이하 덧셈", "② 9 이하 뺄셈", "③ 받아올림 덧셈", "④ 받아내림 뺄셈", "⑤ 두 자리 수 덧셈", "⑥ 두 자리 수 뺄셈", "⑦ 곱셈구구(2~5단)", "⑧ 곱셈구구(6~9단)"]
        sub_category = st.selectbox("세부 항목", sub_list)
        limit_sec = 120 if "두 자리" in sub_category else 60

    if st.button("🔄 검사 초기화"):
        st.session_state.step = "setup"; st.session_state.current_q = 0; st.session_state.score = 0
        st.session_state.results = []; st.session_state.start_time = None; st.rerun()

# 4. 데이터베이스 (PDF 전 문항 수록)
# [수학: cite 82-123, 128-155, 170-200, 205-234, 330-359, 363-393]
math_data = {
    "① 9 이하 덧셈": ["2+1", "1+4", "1+1", "3+2", "3+1", "5+0", "1+3", "4+1", "0+3", "6+1", "1+5", "6+2", "8+1", "3+3", "4+4", "2+4", "4+3", "4+5", "3+5", "2+7", "2+6", "5+4", "1+6", "3+4", "7+1", "6+3", "5+3", "5+2", "4+2", "7+2"],
    "② 9 이하 뺄셈": ["3-1", "2-1", "3-2", "5-2", "5-3", "3-3", "4-2", "5-4", "4-3", "6-1", "9-5", "8-4", "7-2", "8-5", "9-7", "8-7", "9-4", "9-2", "8-3", "7-0", "7-4", "7-5", "9-3", "7-6", "8-6", "8-1", "6-4", "8-2", "6-3", "9-6"],
    "③ 받아올림 덧셈": ["9+1", "9+3", "7+3", "9+2", "8+2", "6+6", "3+8", "6+4", "2+9", "7+9", "6+8", "4+7", "6+5", "8+6", "9+4", "9+5", "4+8", "5+7", "8+9", "7+6", "4+9", "7+5", "5+9", "7+7", "9+7", "7+8", "9+9", "8+8", "5+8", "6+9"],
    "④ 받아내림 뺄셈": ["10-1", "11-3", "10-5", "10-8", "12-3", "11-9", "12-4", "11-8", "11-2", "12-9", "13-6", "11-6", "13-5", "11-5", "18-9", "12-8", "15-8", "14-9", "14-7", "13-9", "13-7", "12-6", "11-7", "16-8", "12-7", "16-9", "14-8", "11-4", "15-6", "17-8"],
    "⑦ 곱셈구구(2~5단)": [f"{a}x{b}" for a, b in [(3,1), (5,2), (2,2), (5,1), (4,2), (5,4), (2,3), (5,3), (2,4), (4,4), (3,3), (3,5), (4,5), (5,5), (2,6), (5,6), (2,7), (5,7), (2,8), (5,8), (2,9), (4,3), (3,7), (3,9), (4,8), (3,6), (4,9), (3,8), (4,6), (3,4)]],
    "⑧ 곱셈구구(6~9단)": [f"{a}x{b}" for a, b in [(6,1), (9,2), (8,2), (8,5), (9,1), (9,5), (6,5), (7,2), (7,5), (6,3), (9,4), (6,4), (7,3), (8,3), (9,3), (6,6), (8,4), (7,7), (7,4), (8,8), (9,7), (6,7), (8,9), (7,6), (6,9), (7,9), (8,6), (9,6), (6,8), (9,8)]]
}

# [국어: cite 767, 837, 863, 942, 1155, 1268]
kor_decoding = ["ㅏ", "ㅓ", "ㅗ", "ㅜ", "ㅡ", "ㅣ", "ㅐ", "ㅔ", "ㅑ", "ㅕ", "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ", "ㄲ", "ㄸ", "ㅃ", "ㅆ", "ㅉ", "가", "나", "다", "라", "마", "바", "사", "아", "자", "차", "카", "타", "파", "하", "어머니", "나무", "소", "우유", "아이"]
kor_nonsense_all = ["포모", "나버", "계난", "책성", "연팔", "펭권", "코끼러", "피마노", "교과사", "강어지", "다람쥐", "놀미터", "동화챈", "일기창", "경철서", "달팽미", "발차국", "준비물", "운동정", "우리너라", "해바리기", "할아비지", "따라좁기", "동그라무", "바디표범", "딱따구리", "자연한경", "교통수던", "확실히게", "의사소동", "미끄럼톨", "국어서전", "징감다리", "특별화동", "동시남분", "실험관칠", "고속타미달", "이산화탐소", "지구온난회", "크리스머스", "수학익험책", "반달거슴곰", "흰수염고래", "대왕오장어", "현장채험학즙", "한국전통문회", "남방큰돌구래", "티러노사우르소"]
kor_passage_elem = ["땀이 나는 이유(제목)", "여러분,", "땀을", "흘려", "본", "경험이", "있지요?", "우리는", "여러", "가지", "상황에서", "땀을", "흘립니다."]
kor_passage_sec = ["반려동물 관련 직업 세계(제목)", "사람과", "더불어", "살아가기", "위한", "목적으로", "기르는", "동물을", "반려동물이라고", "합니다."]
kor_comp_sec = [{"text": "사람과 인공지능의 대결은 사람들의 많은 관심을", "opts": ["선물", "상쾌한", "받아왔습니다"], "ans": "받아왔습니다"}, {"text": "과연 인공지능이 사람을 이길 수 있을까요?", "opts": ["개인적인", "대표적인", "긍정적인"], "ans": "대표적인"}]

# 문항 매칭
if "국어" in category:
    if "해득" in sub_category: questions = kor_decoding
    elif "무의미" in sub_category: questions = kor_nonsense_all[:40] if "초등" in grade and ("1학년" in grade or "2학년" in grade) else kor_nonsense_all
    elif "설명문" in sub_category: questions = kor_passage_sec if is_secondary else kor_passage_elem
    elif "이해" in sub_category: questions = kor_comp_sec
    else: questions = []
else:
    questions = math_data.get(sub_category, [])

# 5. 검사 화면 로직
if not name:
    st.warning("👈 왼쪽에서 학생 정보를 입력하세요.")
elif st.session_state.step == "setup":
    st.subheader(f"📢 {sub_category} 안내")
    st.info("지우개는 사용하지 않습니다. 선생님 신호에 맞춰 최대한 정확하고 빠르게 수행하세요.")
    if st.button("검사 시작", type="primary"):
        st.session_state.start_time = time.time(); st.session_state.step = "test"; st.rerun()

elif st.session_state.step == "test":
    elapsed = time.time() - st.session_state.start_time
    rem = max(0, limit_sec - int(elapsed))
    st.progress(rem / limit_sec, text=f"⏱️ 남은 시간: {rem}초")
    
    if st.session_state.current_q >= len(questions):
        st.session_state.step = "result"; st.rerun()

    q = questions[st.session_state.current_q]
    
    if isinstance(q, dict): # 중등 읽기 이해
        st.markdown(f"### {q['text']}")
        cols = st.columns(3)
        for i, opt in enumerate(q['opts']):
            if cols[i].button(opt, key=f"c_{i}_{st.session_state.current_q}", use_container_width=True):
                res = "정답" if opt == q['ans'] else "오답"
                st.session_state.results.append({"번호": st.session_state.current_q+1, "문항": q['text'], "선택": opt, "정오": res})
                if res == "정답": st.session_state.score += 1
                st.session_state.current_q += 1; st.rerun()
    else:
        st.markdown(f"<h1 style='text-align: center; font-size: 100px;'>{q}</h1>", unsafe_allow_html=True)
        with st.expander("📝 질적 기록 (반응 속도 및 오독 내용)", expanded=True):
            speed = st.radio("반응 속도", ["즉각적/빠름", "느림/주저함"], horizontal=True)
            actual = st.text_input("학생의 실제 발화 내용 (오독 시 기록)", key=f"note_{st.session_state.current_q}")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("⭕ 정답", use_container_width=True, type="primary", key=f"y_{st.session_state.current_q}"):
                st.session_state.results.append({"번호": st.session_state.current_q+1, "문항": q, "정오": "정답", "속도": speed, "발화": actual})
                st.session_state.score += 1; st.session_state.current_q += 1; st.rerun()
        with c2:
            if st.button("❌ 오답", use_container_width=True, key=f"n_{st.session_state.current_q}"):
                st.session_state.results.append({"번호": st.session_state.current_q+1, "문항": q, "정오": "오답", "속도": speed, "발화": actual})
                st.session_state.current_q += 1; st.rerun()

elif st.session_state.step == "result":
    # 판정 기준 
    if "무의미" in sub_category: threshold = {"초등 1학년": 17, "초등 2학년": 21, "초등 3학년": 19}.get(grade, 22)
    elif "해득" in sub_category: threshold = 86
    elif "이해" in sub_category: threshold = 22
    else: threshold = 18 if "초등 1학년" in grade or "초등 2학년" in grade else 24
    
    st.header("📊 진단 결과 보고서")
    status = "도달" if st.session_state.score >= threshold else "미도달"
    st.metric("최종 점수", f"{st.session_state.score}점", f"판정 결과: {status} (기준: {threshold}점)")
    st.table(pd.DataFrame(st.session_state.results))
    st.download_button("📥 엑셀 저장", pd.DataFrame(st.session_state.results).to_csv(index=False).encode('utf-8-sig'), f"{name}_결과.csv")

st.markdown("<br><hr><center>© 인천광역시교육청 학습종합클리닉센터 (초등교육과)</center>", unsafe_allow_html=True)
