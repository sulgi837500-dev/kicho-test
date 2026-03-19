import streamlit as st
import pandas as pd
from datetime import datetime
import time

# 1. 페이지 설정 및 초기화
st.set_page_config(page_title="인천광역시교육청 학습종합클리닉센터", layout="wide")

for key in ['results', 'current_q', 'score', 'step', 'start_time']:
    if key not in st.session_state: 
        st.session_state[key] = [] if key == 'results' else (0 if key in ['current_q', 'score'] else ("setup" if key == 'step' else None))

# 2. 제목 섹션 (공식 명칭 반영)
st.markdown("""
    <div style="text-align: center; background-color: #f0f4f8; padding: 20px; border-radius: 15px; border: 1px solid #d1d9e6;">
        <h4 style="margin-bottom: 5px;">모든 학생의 학습성공을 지원하는</h4>
        <h1 style="color: #0D47A1; margin-top: 0px;">찾아가는 학습지원의 사전·사후 검사 도구</h1>
        <h3 style="color: #333;">인천광역시교육청 학습종합클리닉센터</h3>
        <hr>
    </div>
""", unsafe_allow_html=True)

# 3. 사이드바 설정 (초1~고3 통합)
with st.sidebar:
    st.header("📋 검사 설정")
    name = st.text_input("학생명 (가명)")
    
    # 학년 선택 (초등 1학년 ~ 고등 3학년)
    grade_list = [f"초등 {i}학년" for i in range(1, 7)] + [f"중등 {i}학년" for i in range(1, 4)] + [f"고등 {i}학년" for i in range(1, 4)]
    grade = st.selectbox("학생 학년", grade_list)
    is_secondary = "중등" in grade or "고등" in grade
    
    period = st.radio("검사 시기", ["사전", "사후"])
    st.divider()
    
    category = st.selectbox("대영역", ["기초 국어 (읽기·쓰기 유창성)", "기초 수학 (연산 유창성)"])
    
    # 영역별 세부 항목 (PDF 내용 전수 반영)
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

# 4. 전 문항 데이터베이스
# [수학 문항 전수 로드]
math_addition_9 = ["2+1", "1+4", "1+1", "3+2", "3+1", "5+0", "1+3", "4+1", "0+3", "6+1", "1+5", "6+2", "8+1", "3+3", "4+4", "2+4", "4+3", "4+5", "3+5", "2+7", "2+6", "5+4", "1+6", "3+4", "7+1", "6+3", "5+3", "5+2", "4+2", "7+2"]
math_sub_9 = ["3-1", "2-1", "3-2", "5-2", "5-3", "3-3", "4-2", "5-4", "4-3", "6-1", "9-5", "8-4", "7-2", "8-5", "9-7", "8-7", "9-4", "9-2", "8-3", "7-0", "7-4", "7-5", "9-3", "7-6", "8-6", "8-1", "6-4", "8-2", "6-3", "9-6"]

# [국어 문항 전수 로드]
kor_nonsense_elem = ["포모", "나버", "계난", "책성", "연팔", "펭권", "코끼러", "피마노", "교과사", "강어지", "다람쥐", "놀미터", "동화챈", "일기창", "경철서", "달팽미", "발차국", "준비물", "운동정", "우리너라", "해바리기", "할아비지", "따라좁기", "동그라무", "바디표범", "딱따구리", "체육대화", "초등학고", "확실히게", "숨바꼬질", "미끄럼톨", "국어서전", "징감다리", "특별화동", "동시남분", "실험관칠", "고속타미달", "이산화탐소", "현장체험학습", "한국전동문회"]
kor_nonsense_sec = kor_nonsense_elem + ["수학익험책", "반달거슴곰", "흰수염고래", "대왕오장어", "현장채험학즙", "한국전통문회", "남방큰돌구래", "티러노사우르소"]
kor_passage_elem = ["땀이 나는 이유(제목)", "여러분,", "땀을", "흘려", "본", "경험이", "있지요?", "우리는", "여러", "가지", "상황에서", "땀을", "흘립니다."]
kor_passage_sec = ["반려동물 관련 직업 세계(제목)", "사람과", "더불어", "살아가기", "위한", "목적으로", "기르는", "동물을", "반려동물이라고", "합니다."]
kor_comprehension = [
    {"text": "사람과 인공지능의 대결은 사람들의 많은 관심을", "opts": ["선물", "상쾌한", "받아왔습니다"], "ans": "받아왔습니다"},
    {"text": "과연 인공지능이 사람을 이길 수 있을까요?", "opts": ["개인적인", "대표적인", "긍정적인"], "ans": "대표적인"}
]

# 문항 할당 로직
if "국어" in category:
    if "무의미" in sub_category: questions = kor_nonsense_sec if is_secondary else kor_nonsense_elem
    elif "설명문" in sub_category: questions = kor_passage_sec if is_secondary else kor_passage_elem
    elif "이해" in sub_category: questions = kor_comprehension
    else: questions = ["준비 중입니다."]
else:
    if "덧셈" in sub_category: questions = math_addition_9
    elif "뺄셈" in sub_category: questions = math_sub_9
    else: questions = ["준비 중입니다."]

# 5. 검사 실행 화면
if not name:
    st.warning("👈 왼쪽 사이드바에 학생 정보를 입력해 주세요.")
elif st.session_state.step == "setup":
    st.subheader(f"📢 {sub_category} 학생 안내")
    st.info("지우개는 사용하지 않습니다. 선생님 신호에 맞춰 최대한 정확하고 빠르게 수행하세요.")
    if st.button("검사 시작", type="primary"):
        st.session_state.start_time = time.time(); st.session_state.step = "test"; st.rerun()

elif st.session_state.step == "test":
    elapsed = time.time() - st.session_state.start_time
    rem = max(0, limit_sec - int(elapsed))
    st.progress(rem / limit_sec, text=f"⏱️ 남은 시간: {rem}초")
    
    if rem <= 0 or st.session_state.current_q >= len(questions):
        st.session_state.step = "result"; st.rerun()

    q = questions[st.session_state.current_q]
    
    if "이해" in sub_category:
        st.markdown(f"### {q['text']}")
        cols = st.columns(3)
        for i, opt in enumerate(q['opts']):
            if cols[i].button(opt, key=f"btn_{i}_{st.session_state.current_q}", use_container_width=True):
                is_correct = "정답" if opt == q['ans'] else "오답"
                st.session_state.results.append({"번호": st.session_state.current_q+1, "문항": q['text'], "선택": opt, "정오": is_correct})
                if is_correct == "정답": st.session_state.score += 1
                st.session_state.current_q += 1; st.rerun()
    else:
        st.markdown(f"<h1 style='text-align: center; font-size: 100px;'>{q}</h1>", unsafe_allow_html=True)
        with st.expander("📝 질적 관찰 기록 (반응 속도 및 오독 내용)", expanded=True):
            speed = st.radio("반응 속도", ["즉각적/빠름", "느림/주저함"], horizontal=True)
            actual = st.text_input("학생의 실제 발화 내용 (오독 시 기록)", key=f"note_{st.session_state.current_q}")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("⭕ 정답", use_container_width=True, type="primary", key=f"yes_{st.session_state.current_q}"):
                st.session_state.results.append({"번호": st.session_state.current_q+1, "문항": q, "정오": "정답", "속도": speed, "발화": actual})
                st.session_state.score += 1; st.session_state.current_q += 1; st.rerun()
        with c2:
            if st.button("❌ 오답", use_container_width=True, key=f"no_{st.session_state.current_q}"):
                st.session_state.results.append({"번호": st.session_state.current_q+1, "문항": q, "정오": "오답", "속도": speed, "발화": actual})
                st.session_state.current_q += 1; st.rerun()

elif st.session_state.step == "result":
    # 도달 기준 판정 (PDF 근거)
    if "무의미" in sub_category:
        threshold = {"초등 1학년": 17, "초등 2학년": 21, "초등 3학년": 19}.get(grade, 22)
    elif "이해" in sub_category: threshold = 22
    else: threshold = 18 if grade in ["초등 1학년", "초등 2학년"] else 24
    
    st.header("📊 진단 결과 보고서")
    status = "도달" if st.session_state.score >= threshold else "미도달"
    st.metric(f"{sub_category} 최종 점수", f"{st.session_state.score}점", f"판정 결과: {status} (기준: {threshold}점)")
    
    df = pd.DataFrame(st.session_state.results)
    st.table(df)
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 상세 문항 기록 엑셀 저장", csv, f"{name}_{sub_category}_결과.csv")

st.markdown("<br><hr><center>© 인천광역시교육청 학습종합클리닉센터 (초등교육과)</center>", unsafe_allow_html=True)
