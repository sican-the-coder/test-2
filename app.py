import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

# 1. 페이지 설정
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

# 2. 프리텐다드 폰트 적용 및 고도화된 스타일링
st.markdown("""
    <link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
    
    <style>
    /* 전체 배경 및 프리텐다드 폰트 강제 적용 */
    body, .stApp, button, input, select, textarea {
        font-family: "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont, system-ui, Roboto, "Helvetica Neue", "Segoe UI", "Apple SD Gothic Neo", "Noto Sans KR", "Malgun Gothic", "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", sans-serif !important;
    }

    .stApp { background-color: #f2f2f2; }

    /* PC 중앙 정렬 및 폭 제한 */
    @media (min-width: 1200px) {
        .block-container {
            max-width: 1200px !important;
            padding-top: 1.5rem !important;
            margin: auto;
        }
    }

    /* 섹션 타이틀 바 (AAGAG 오마주) */
    .section-bar { 
        background-color: #55587c; 
        color: white; 
        padding: 6px 12px; 
        font-size: 13px; 
        font-weight: 700; /* 프리텐다드 굵은 서체 활용 */
        display: flex; 
        justify-content: space-between; 
        border-radius: 3px 3px 0 0; 
        letter-spacing: -0.02em;
    }

    /* 리스트 컨테이너 */
    .list-container { 
        background-color: white; 
        border: 1px solid #ddd; 
        margin-bottom: 18px; 
        border-top: none; 
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }

    /* 리스트 아이템 디자인 (가독성 강화) */
    .list-item { 
        display: flex; 
        padding: 7px 12px; 
        border-bottom: 1px solid #f0f0f0; 
        font-size: 12.5px; 
        align-items: center; 
        transition: background 0.1s; 
    }
    .list-item:hover { background-color: #f8f9fa; }

    .tag-biz { background: #eef2ff; color: #4338ca; padding: 2px 5px; border-radius: 3px; font-size: 10px; margin-right: 8px; font-weight: 600; }
    .tag-global { background: #fff1f2; color: #e11d48; padding: 2px 5px; border-radius: 3px; font-size: 10px; margin-right: 8px; font-weight: 600; }
    
    .title-text { 
        color: #333; 
        font-weight: 600; 
        white-space: nowrap; 
        overflow: hidden; 
        text-overflow: ellipsis; 
        flex-grow: 1; 
        letter-spacing: -0.03em; /* 프리텐다드 특유의 자간 조정 */
    }

    .rank-num { font-weight: 800; width: 22px; color: #adb5bd; text-align: center; margin-right: 10px; font-size: 14px; }
    .blue { color: #3b82f6 !important; } 
    .red { color: #ef4444 !important; }
    .green { color: #10b981 !important; }

    /* 메인 로고 바 */
    .main-logo-bar {
        background-color: #3e4156;
        padding: 12px 20px;
        color: white;
        border-radius: 5px;
        margin-bottom: 20px;
        font-weight: 800;
        font-size: 20px;
        letter-spacing: -0.05em;
    }
    </style>
""", unsafe_allow_html=True)

# 3. 데이터 로직 (생략/유지 - 이전과 동일)
@st.cache_data(ttl=600)
def fetch_all_integrated_data():
    # 데이터 구조 시뮬레이션 (담당자님이 말씀하신 뉴스 사이트 + 글로벌 포함)
    data = []
    sources = [
        ("지디넷", "비즈니스"), ("MTN", "비즈니스"), ("딜사이트", "비즈니스"),
        ("IGN", "해외매체"), ("VGC", "해외매체"), ("Kotaku", "해외매체"),
        ("인벤", "커뮤니티"), ("루리웹", "커뮤니티"), ("펨코", "커뮤니티")
    ]
    for name, cat in sources:
        for i in range(5):
            title = f"{name}의 실시간 주요 이슈 분석 #{i+1}"
            if cat == "해외매체": title = f"🌏 [번역] {name} 글로벌 리포트: 주요 게임 시장 동향 {i+1}"
            data.append({
                "title": title, "source": name, "category": cat,
                "views": 10000 - (i*1000), "likes": 500 - (i*50), "cmts": 100 - (i*10), "time": i*10
            })
    return pd.DataFrame(data)

df = fetch_all_integrated_data()

# --- 화면 렌더링 ---

st.markdown('<div class="main-logo-bar">AAGIG: Game Insight Ground</div>', unsafe_allow_html=True)

# 상단 그리드
c1, c2 = st.columns(2)

def draw_box(header, data, is_global=False):
    tag_class = "tag-global" if is_global else "tag-biz"
    st.markdown(f'<div class="section-bar"><span>{header}</span><span style="font-weight:400; font-size:11px;">더 보기</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="list-container">', unsafe_allow_html=True)
    for _, r in data.head(7).iterrows():
        st.markdown(f"""
            <div class="list-item">
                <span class="{tag_class}">{r['source']}</span>
                <span class="title-text">{r['title']}</span>
                <span style="font-size:10px; color:#999; margin-left:10px; min-width:40px;">{r['time']}m</span>
            </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c1:
    draw_box("📈 비즈니스/IT (지디넷, MTN, 딜사이트)", df[df['category'] == '비즈니스'])
    draw_box("🌐 글로벌 트렌드 (IGN, VGC 번역)", df[df['category'] == '해외매체'], is_global=True)

with c2:
    draw_box("🔥 국내 커뮤니티 (인벤, 루리웹, 펨코)", df[df['category'] == '커뮤니티'])
    draw_box("📊 하트 많이 받은 이슈 (24H)", df.sort_values('likes', ascending=False))

# 하단 랭킹
st.write("")
b1, b2, b3 = st.columns(3)

def draw_ranking(header, data, score_col, color_class):
    st.markdown(f'<div class="section-bar"><span>{header}</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="list-container">', unsafe_allow_html=True)
    for i, r in enumerate(data.sort_values(score_col, ascending=False).head(15).iterrows()):
        num = i + 1
        st.markdown(f"""
            <div class="list-item">
                <span class="rank-num {color_class if num <= 5 else ''}">{num}</span>
                <span class="title-text">{r[1]['title']}</span>
                <span style="font-size:10px; color:#aaa; min-width:30px; text-align:right;">{int(r[1][score_col])}</span>
            </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with b1: draw_ranking("종합 조회수 랭킹", df, 'views', 'blue')
with b2: draw_ranking("시장 주목도 (Likes)", df, 'likes', 'red')
with b3: draw_ranking("여론 활성도 (Comments)", df, 'cmts', 'green')
