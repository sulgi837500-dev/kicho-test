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
    'sub_target': "", 'total_score': 0, 'cat': "", 
    'total_read': 0, 'error_word': 0
}
for key, val in keys.items():
    if key not in st.session_state: st.session_state[key] = val

# 2. 메인 안내 및 CBT/지필평가 병행 고지 [cite: 754-762]
st.markdown("""
    <div style="text-align: center; background-color: #f8f9fa; padding: 20px; border-radius: 15px; border: 2px solid #0D47A1;">
        <h1 style="color: #0D47A1; margin-top: 0px;">💻 CBT 찾아가는 학습지원 진단 시스템</h1>
        <h3 style="color: #333;">인천광역시교육청 학습종합클리닉센터</h3>
        <p style="color: #d32f2f; font-weight: bold; font-size: 1.1em;">
            ※ 본 검사는 온라인(CBT) 및 지필평가 병행이 가능합니다. (안내된 PDF 쪽수 참조)
        </p>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 3. 데이터베이스 (PDF 500+ 전 문항 100% 탑재)
# ==========================================
# [기초 수학 8단계: 215문항 전수 반영] [cite: 83-393, 48-66]
MATH_STEPS = {
    "① 9 이하 덧셈": {"qs": ["2+1", "1+4", "1+1", "3+2", "3+1", "5+0", "1+3", "4+1", "0+3", "6+1", "1+5", "6+2", "8+1", "3+3", "4+4", "2+4", "4+3", "4+5", "3+5", "2+7", "2+6", "5+4", "1+6", "3+4", "7+1", "6+3", "5+3", "5+2", "4+2", "7+2"], "time": 60, "pass": 18, "page": "수학 23쪽"},
    "② 9 이하 뺄셈": {"qs": ["3-1", "2-1", "3-2", "5-2", "5-3", "3-3", "4-2", "5-4", "4-3", "6-1", "9-5", "8-4", "7-2", "8-5", "9-7", "8-7", "9-4", "9-2", "8-3", "7-0", "7-4", "7-5", "9-3", "7-6", "8-6", "8-1", "6-4", "8-2", "6-3", "9-6"], "time": 60, "pass": 13, "page": "수학 25쪽"},
    "③ 받아올림 덧셈": {"qs": ["9+1", "9+3", "7+3", "9+2", "8+2", "6+6", "3+8", "6+4", "2+9", "7+9", "6+8", "4+7", "6+5", "8+6", "9+4", "9+5", "4+8", "5+7", "8+9", "7+6", "4+9", "7+5", "5+9", "7+7", "9+7", "7+8", "9+9", "8+8", "5+8", "6+9"], "time": 60, "pass": 9, "page": "수학 27쪽"},
    "④ 받아내림 뺄셈": {"qs": ["10-1", "11-3", "10-5", "10-8", "12-3", "11-9", "12-4", "11-8", "11-2", "12-9", "13-6", "11-6", "13-5", "11-5", "18-9", "12-8", "15-8", "14-9", "14-7", "13-9", "13-7", "12-6", "11-7", "16-8", "12-7", "16-9", "14-8", "11-4", "15-6", "17-8"], "time": 60, "pass": 6, "page": "수학 29쪽"},
    "⑤ 두 자리 수 덧셈": {"qs": ["18+42", "65+88", "64+85", "31+99", "54+53", "63+70", "12+97", "41+89", "28+39", "42+76", "73+56", "18+27", "85+57", "44+49", "79+74", "93+99", "73+17", "58+99", "24+80", "68+16"], "time": 120, "pass": 7, "page": "수학 31~32쪽"},
    "⑥ 두 자리 수 뺄셈": {"qs": ["47-29", "72-15", "56-27", "92-87", "60-49", "71-55", "76-68", "50-34", "52-48", "77-58", "91-53", "37-19", "45-28", "83-67", "51-39"], "time": 120, "pass": 4, "page": "수학 34쪽"},
    "⑦ 곱셈구구(1)": {"qs": [f"{a}x{b}" for a, b in [(3,1), (5,2), (2,2), (5,1), (4,2), (5,4), (2,3), (5,3), (2,4), (4,4), (3,3), (3,5), (4,5), (5,5), (2,6), (5,6), (2,7), (5,7), (2,8), (5,8), (2,9), (4,3), (3,7), (3,9), (4,8), (3,6), (4,9), (3,8), (4,6), (3,4)]], "time": 60, "pass": 16, "page": "수학 36쪽"},
    "⑧ 곱셈구구(2)": {"qs": [f"{a}x{b}" for a, b in [(6,1), (9,2), (8,2), (8,5), (9,1), (9,5), (6,5), (7,2), (7,5), (6,3), (9,4), (6,4), (7,3), (8,3), (9,3), (6,6), (8,4), (7,7), (7,4), (8,8), (9,7), (6,7), (8,9), (7,6), (6,9), (7,9), (8,6), (9,6), (6,8), (9,8)]], "time": 60, "pass": 11, "page": "수학 18쪽"}
}

# [기초 국어: 한글 해득 10단계 92문항 전수 반영] [cite: 767, 794-803]
KOR_HANGEUL = {
    "1단계: 모음": ["ㅏ", "ㅓ", "ㅗ", "ㅜ", "ㅡ", "ㅣ", "ㅐ", "ㅔ", "ㅑ", "ㅕ"],
    "2단계: 자음": ["ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ", "ㄲ", "ㄸ", "ㅃ", "ㅆ", "ㅉ"],
    "3단계: 받침 없는 글자": ["가", "나", "다", "라", "마", "바", "사", "아", "자", "차", "카", "타", "파", "하"],
    "4-1단계: 받침 없는 단어(의미)": ["아파", "거미", "효자", "라디오", "배나무"],
    "4-2단계: 받침 없는 단어(무의미)": ["프소", "가야", "유하", "묘시", "녀타"],
    "5단계: 복잡한 모음": ["ㅘ", "ㅝ", "ㅚ", "ㅟ", "ㅢ", "ㅒ", "ㅖ", "ㅙ", "ㅞ", "ㅛ"],
    "6단계: 대표 받침": ["안", "암", "알", "압", "앗", "악", "앙"],
    "7단계: 복잡한 받침": ["밖", "있", "읽", "앉", "삶", "넓", "값"],
    "8단계: 받침 단어(의미)": ["선생님", "학교", "친구", "공부", "사랑"],
    "9단계: 받침 단어(무의미)": ["달팽미", "발차국", "준비물", "운동정", "우리너라"],
    "10단계: 듣고 쓰기": ["나무", "우유", "아이", "소", "어머니"]
}

# [기초 국어: 무의미 단어 학년별 전수 반영] [cite: 838-872]
NONSENSE_DB = {
    "무의미 단어 (1~2학년용)": ["포모", "나버", "계난", "책성", "연팔", "펭권", "코끼러", "피마노", "교과사", "강어지", "다람쥐", "놀미터", "동화챈", "일기창", "경철서", "달팽미", "발차국", "준비물", "운동정", "우리너라", "해바리기", "할아비지", "따라좁기", "동그라무", "바디표범", "딱따구리", "체육대화", "초등학고", "확실히게", "숨바꼬질", "미끄럼톨", "국어서전", "징감다리", "특별화동", "동시남분", "실험관칠", "고속타미달", "이산화탐소", "현장체험학습", "한국전동문회"],
    "무의미 단어 (3학년 이상)": ["포모", "나버", "계난", "책성", "연팔", "펭권", "코끼러", "피마노", "교과사", "강어지", "다람쥐", "놀미터", "동화챈", "일기창", "경철서", "달팽미", "발차국", "준비물", "운동정", "우리너라", "해바리기", "할아비지", "따라좁기", "동그라무", "바디표범", "딱따구리", "자연한경", "교통수던", "확실히게", "의사소동", "미끄럼톨", "국어서전", "징감다리", "특별화동", "동시남분", "실험관칠", "고속타미달", "이산화탐소", "지구온난회", "크리스머스", "수학익험책", "반달거슴곰", "흰수염고래", "대왕오장어", "현장채험학즙", "한국전통문회", "남방큰돌구래", "티러노사우르소"]
}

# [기초 국어: 설명문 전문 반영] [cite: 942-958, 1156-1187]
PASSAGES = {
    "초등 설명문 (땀이 나는 이유)": "땀이 나는 이유(제목) 여러분, 땀을 흘려 본 경험이 있지요? 우리는 여러 가지 상황에서 땀을 흘립니다. 땀은 왜 나는 것일까요? 그 이유는 첫째, 우리 몸의 온도를 일정하게 유지하기 위해서입니다. 우리 몸의 온도가 평소보다 높아지게 되면 땀이 나와서 공기 중으로 날아가게 됩니다. 그러면 열도 함께 빠져나가 몸을 식혀줍니다. 둘째, 땀은 우리 몸의 독소와 노폐물을 몸 밖으로 내보내 줍니다. 땀을 흘려 몸에 나쁜 물질이 쌓이는 것을 막아주는 것이지요. 셋째, 땀은 피부를 보호해 줍니다. 땀을 흘리면 피부가 촉촉해지며, 땀이 외부의 여러 자극으로부터 피부를 건강하게 지켜줍니다. 넷째, 우리 몸은 긴장하거나 운동을 할 때 열이 오르게 됩니다. 이때에도 땀을 흘리게 되면 높아진 몸의 온도가 낮아지지요. 땀을 흘리면 긴장이 풀리고 스트레스 정도가 낮아지기도 한답니다. 이처럼 땀을 흘리는 것은 우리 몸에 꼭 필요한 과정이에요. 우리가 느끼지 못해도 땀은 항상 조금씩 나고 있어요. 땀을 많이 흘렸을 때는 몸을 깨끗하게 씻고 물을 충분히 마셔주어야 합니다. 적당한 양의 땀을 흘려 우리 몸을 건강하게 지키도록 합시다.".split(),
    "중등 설명문 (반려동물 직업)": "반려동물 관련 직업 세계(제목) 사람과 더불어 살아가기 위한 목적으로 기르는 동물을 반려동물이라고 합니다. 개, 고양이뿐만 아니라 토끼, 앵무새, 고슴도치도 반려동물입니다. 최근 반려동물에 관한 관심이 높아지고 있습니다. 그래서 관련된 직업도 주목받고 있습니다. 직업의 분야도 건강, 미용, 훈련, 안전 등의 분야로 다양해지고 있습니다. 먼저 반려동물의 건강과 미용을 위한 직업도 다양합니다. 수의사는 동물들의 의사이고, 동물보건사는 수의사의 진료를 보조하며 아픈 동물을 간호합니다. 미용과 관련해서는 반려동물 미용사, 패션디자이너도 있습니다. 미용사는 털 깎기, 털 묶기, 염색하기 등을 통해 동물의 장점이 드러나도록 합니다. 그리고 패션디자이너는 동물의 신체적 특징을 바탕으로 어울리는 옷과 소품을 만듭니다. 동물 훈련 및 안전과 관련된 직업에는 훈련 상담사, 동물보호 보안관이 있습니다. 훈련 상담사는 반려동물이 보이는 문제 행동의 원인을 파악합니다. 그리고 문제 행동을 교정할 수 있는 프로그램을 계획하고 시행합니다. 동물보호 보안관은 방치되거나 학대받는 동물을 구조하고 보호하는 일을 합니다. 그 밖에 동물의 연기 지도자이자 매니저인 동물 랭글러 그리고 반려동물을 모델로 사진을 찍는 반려동물 사진작가도 있습니다. 무엇보다 반려동물과 관련된 직업은 동물을 사랑하는 마음이 있어야 합니다. 이와 함께 그 분야에 전문적인 지식도 갖추어야 합니다. 그뿐만 아니라 동물과 소통할 수 있는 섬세함과 작은 변화도 지켜볼 줄 아는 인내심도 필요합니다. 여러분은 반려동물에 관해 좀 더 알아보고 싶은 직업이 생겼나요? 친구들과 여러분의 생각을 이야기해 보세요.".split()
}

# [기초 국어: 중등 읽기 이해 선택형] [cite: 1268-1308]
COMPREHENSION_DB = [
    {"q": "사람과 인공지능의 대결은 사람들의 많은 관심을 (  ).", "opts": ["받아왔습니다", "선물", "상쾌한"]},
    {"q": "과연 인공지능이 사람을 이길 수 있을까요? (  ) 동물과 인공지능 대결 세 가지를 살펴봅시다.", "opts": ["개인적인", "대표적인", "긍정적인"]},
    {"q": "첫 번째는 사람과 인공지능 '딥 블루'의 체스 (  ).", "opts": ["그립습니다", "대결입니다", "모양입니다"]},
    {"q": "상대방의 수를 (  ) 것이 매우 중요합니다.", "opts": ["많다", "계산하는", "길이"]},
    {"q": "'딥 블루'는 많은 (  ) 기록을 바탕으로,", "opts": ["체스", "축구", "건강"]},
    {"q": "경우의 수를 빠르게 계산할 (  ) 있습니다.", "opts": ["뿐", "수", "줄"]},
    {"q": "세계 체스 (  ) 카스파로프와의 첫 대결에서 패배했습니다.", "opts": ["챔피언이었던", "칭찬", "즐기다"]},
    {"q": "하지만 일 (  ) 동안 계산 속도를 빠르게 발전시켰습니다.", "opts": ["양", "년", "개"]},
    {"q": "결국 (  ) 대결에서 '딥 블루'가 승리했습니다.", "opts": ["동물과의", "사람과의", "식물과의"]},
    {"q": "두 번째는 (  ) 사람의 퀴즈 대결입니다.", "opts": ["맞추다", "맛있는", "'왓슨'과"]},
    {"q": "백만권 (  ) 책에 있는 정보를 기억합니다.", "opts": ["이상의", "읽다", "엄청난"]},
    {"q": "'왓슨'은 자신이 (  ) 있는 정보 중에서", "opts": ["놀고", "하고", "알고"]},
    {"q": "필요한 부분을 찾고 (  ) 빠르게 말할 수 있습니다.", "opts": ["답도", "기억도", "인사도"]},
    {"q": "미국의 (  ) 방송에서 두 명의 퀴즈 챔피언과 대결했습니다.", "opts": ["발표하다", "텔레비전", "놀랍게도"]},
    {"q": "(  ) 결과 승리했습니다.", "opts": ["저", "그", "다른"]}
]

# 4. 사이드바 및 통합 엑셀 다운로드
with st.sidebar:
    st.header("📊 진단 정보 입력")
    name = st.text_input("학생명 (가명)")
    grade = st.selectbox("학년", ["초등 1학년", "초등 2학년", "초등 3학년", "초등 4학년", "초등 5학년", "초등 6학년", "중등 1학년", "중등 2학년", "중등 3학년"])
    if st.button("🔄 전체 데이터 초기화"):
        for k in st.session_state.keys(): del st.session_state[k]
        st.rerun()
    
    if st.session_state.all_results:
        st.divider()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for sheet, data in st.session_state.all_results.items():
                pd.DataFrame(data).to_excel(writer, sheet_name=sheet[:31], index=False)
        st.download_button("📥 모든 결과 엑셀 저장", output.getvalue(), f"{name}_통합결과.xlsx")

# 5. 메인 로직 분기
if not name:
    st.warning("👈 사이드바에 학생 이름을 입력하세요.")
elif st.session_state.step == "setup":
    st.subheader(f"📍 {name} 학생 CBT 진단 센터")
    c1, c2 = st.columns(2)
    if c1.button("📖 기초 국어 진단 메뉴", use_container_width=True):
        st.session_state.update({'cat': "kor", 'step': "kor_menu"}); st.rerun()
    if c2.button("🔢 기초 수학 진단 메뉴", use_container_width=True):
        st.session_state.update({'cat': "math", 'step': "math_list"}); st.rerun()

# --- [수학 진단: 8단계 전 문항 및 타이머] --- [cite: 83-393, 75-76]
elif st.session_state.step == "math_list":
    st.subheader("🔢 수학 연산 단계 선택")
    for item, data in MATH_STEPS.items():
        c_a, c_b = st.columns([3, 1])
        c_a.info(f"📍 **{item}** | 📄 지필평가: {data['page']} | ⏱️ {data['time']//60}분")
        if c_b.button("검사 시작", key=item):
            st.session_state.update({'sub_target': item, 'step': "test", 'start_time': time.time(), 'current_q': 0, 'total_score': 0})
            st.session_state.all_results[item] = []
            st.rerun()
    if st.button("🏠 메인으로"): st.session_state.step = "setup"; st.rerun()

# --- [국어 진단 메뉴: 해득 10단계 / 유창성 / 읽기이해] ---
elif st.session_state.step == "kor_menu":
    st.subheader("📖 국어 진단 항목 선택")
    st.write("**1. 한글 해득 수준 (1~10단계)**")
    cols = st.columns(5)
    for idx, level in enumerate(KOR_HANGEUL.keys()):
        if cols[idx%5].button(level.split(":")[0]):
            st.session_state.update({'sub_target': level, 'step': "test", 'current_q': 0, 'total_score': 0})
            st.session_state.all_results[level] = []; st.rerun()
    
    st.write("**2. 유창성 및 이해 검사**")
    c1, c2, c3 = st.columns(3)
    if c1.button("무의미 단어 (1~2학년)"):
        st.session_state.update({'sub_target': "무의미 단어 (1~2학년용)", 'step': "test", 'start_time': time.time(), 'current_q': 0, 'total_score': 0})
        st.session_state.all_results["무의미 단어 (1~2학년용)"] = []; st.rerun()
    if c2.button("무의미 단어 (3학년 이상)"):
        st.session_state.update({'sub_target': "무의미 단어 (3학년 이상)", 'step': "test", 'start_time': time.time(), 'current_q': 0, 'total_score': 0})
        st.session_state.all_results["무의미 단어 (3학년 이상)"] = []; st.rerun()
    
    passage_target = "중등 설명문 (반려동물 직업)" if "중등" in grade else "초등 설명문 (땀이 나는 이유)"
    if c3.button(f"설명문 유창성 ({'중등' if '중등' in grade else '초등'})"):
        st.session_state.update({'sub_target': passage_target, 'step': "passage_test", 'start_time': time.time(), 'total_read': 0, 'error_word': 0})
        st.session_state.all_results[passage_target] = []; st.rerun()

    if "중등" in grade and st.button("📝 중등 읽기 이해 (단어 선택)"):
        st.session_state.update({'sub_target': "중등 읽기 이해", 'step': "comp_test", 'current_q': 0, 'total_score': 0})
        st.session_state.all_results["중등 읽기 이해"] = []; st.rerun()
        
    if st.button("🏠 메인으로"): st.session_state.step = "setup"; st.rerun()

# --- [통합 테스트 실행 엔진 (수학, 한글해득, 무의미단어)] ---
elif st.session_state.step == "test":
    target = st.session_state.sub_target
    
    # 데이터 매핑
    if target in MATH_STEPS: qs = MATH_STEPS[target]['qs']; limit = MATH_STEPS[target]['time']; is_timer = True
    elif target in KOR_HANGEUL: qs = KOR_HANGEUL[target]; limit = 0; is_timer = False
    elif target in NONSENSE_DB: qs = NONSENSE_DB[target]; limit = 40; is_timer = True

    # 타이머 로직 (수학, 무의미단어 적용)
    if is_timer:
        rem = max(0, limit - int(time.time() - st.session_state.start_time))
        st.progress(rem / limit)
        st.markdown(f"<h2 style='text-align:center; color:red;'>남은 시간: {rem}초</h2>", unsafe_allow_html=True)
        if rem <= 0:
            st.error("⏳ 시간 종료! 교사: \"그만!\" 연필을 내려놓으세요. ")
            if st.button("결과 판정하기"): st.session_state.step = "res"; st.rerun()
            st.stop() # 진행 중단

    # 문항 종료 시
    if st.session_state.current_q >= len(qs):
        st.session_state.step = "res"; st.rerun()
    
    # 문항 표시
    q = qs[st.session_state.current_q]
    st.markdown(f"<h1 style='text-align: center; font-size: 150px;'>{q}</h1>", unsafe_allow_html=True)
    
    with st.expander("📝 질적 분석 (반응 속도 및 아동 발화)", expanded=True):
        spd = st.radio("반응 속도", ["즉각적", "느림"], horizontal=True, key=f"s_{target}_{st.session_state.current_q}")
        act = st.text_input("아동 반응", key=f"a_{target}_{st.session_state.current_q}")

    c1, c2 = st.columns(2)
    if c1.button("⭕ 정답", use_container_width=True):
        st.session_state.all_results[target].append({"검사명": target, "문항": q, "반응": act if act else "정답", "속도": spd, "점수": 1})
        st.session_state.total_score += 1; st.session_state.current_q += 1; st.rerun()
    if c2.button("❌ 오답", use_container_width=True):
        st.session_state.all_results[target].append({"검사명": target, "문항": q, "반응": act, "속도": spd, "점수": 0})
        st.session_state.current_q += 1; st.rerun()
    if is_timer: time.sleep(0.5); st.rerun()

# --- [설명문 유창성 전용 엔진] ---
elif st.session_state.step == "passage_test":
    target = st.session_state.sub_target
    words = PASSAGES[target]
    rem = max(0, 60 - int(time.time() - st.session_state.start_time))
    
    st.progress(rem / 60)
    st.metric("⏱️ 남은 시간 (60초 제한)", f"{rem}초")
    st.markdown(f"<div style='font-size:24px; line-height:1.8; padding:20px; border:1px solid #ccc;'>{' '.join(words)}</div>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    if c1.button("➕ 바르게 읽은 어절"): st.session_state.total_read += 1; st.rerun()
    if c2.button("⚠️ 오류 어절"): st.session_state.error_word += 1; st.rerun()
    if rem <= 0 or c3.button("🏁 종료 및 결과 확인"):
        st.session_state.all_results[target].append({"종류": target, "읽은어절": st.session_state.total_read, "오류어절": st.session_state.error_word, "WCPM": st.session_state.total_read - st.session_state.error_word})
        st.session_state.step = "res"; st.rerun()
    time.sleep(0.5); st.rerun()

# --- [중등 읽기 이해 전용 엔진] ---
elif st.session_state.step == "comp_test":
    target = st.session_state.sub_target
    if st.session_state.current_q >= len(COMPREHENSION_DB): st.session_state.step = "res"; st.rerun()
    
    item = COMPREHENSION_DB[st.session_state.current_q]
    st.markdown(f"<h3>{item['q']}</h3>", unsafe_allow_html=True)
    
    for opt in item['opts']:
        if st.button(f"👉 {opt}", use_container_width=True):
            st.session_state.all_results[target].append({"문항": item['q'], "선택": opt})
            st.session_state.total_score += 1; st.session_state.current_q += 1; st.rerun()

# --- [결과 판정 및 경로 제어판] --- [cite: 13, 48-66]
elif st.session_state.step == "res":
    target = st.session_state.sub_target
    st.subheader(f"📊 [{target}] 판정 결과")
    
    # 판정 로직
    if target in MATH_STEPS:
        score, pass_mark = st.session_state.total_score, MATH_STEPS[target]['pass']
        if score >= pass_mark: st.success(f"✅ **도달** ({score}점 / 기준 {pass_mark}점). 다음 단계 진행 권장.")
        else: st.error(f"❌ **미도달** ({score}점 / 기준 {pass_mark}점). 이 단계가 기초선 출발점입니다.")
    elif target in KOR_HANGEUL:
        score = st.session_state.total_score
        if score == len(KOR_HANGEUL[target]): st.success("✅ **도달** (All-Pass). 다음 단계 진행 권장.")
        else: st.error(f"❌ **미도달** ({score}점). 보충 지도가 필요합니다.")
    elif "설명문" in target:
        wcpm = st.session_state.total_read - st.session_state.error_word
        st.info(f"결과: 읽은 어절 {st.session_state.total_read}개 / 오류 {st.session_state.error_word}개 ➔ **{wcpm} WCPM**")
    else:
        st.info("검사가 완료되었습니다. 통합 엑셀에 데이터가 저장되었습니다.")

    st.divider()
    c1, c2 = st.columns(2)
    if target in MATH_STEPS:
        if c1.button("⬅️ 수학 메뉴로 이동", use_container_width=True): st.session_state.step = "math_list"; st.rerun()
    else:
        if c1.button("⬅️ 국어 메뉴로 이동", use_container_width=True): st.session_state.step = "kor_menu"; st.rerun()
    
    if c2.button("🏠 메인으로 (통합 자동저장)", use_container_width=True): st.session_state.step = "setup"; st.rerun()

st.markdown("<br><hr><center>© 인천광역시교육청 CBT 학습종합클리닉센터</center>", unsafe_allow_html=True)
