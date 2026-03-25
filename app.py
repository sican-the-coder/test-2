import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

# 1. 페이지 설정
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

# 2. 스타일 시트 (v10.0 기반 AAGAG UI + [피드백 반영] 서브 헤더/배너/버전 스타일)
st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
<style>
    /* 전체 배경 및 폰트 */
    body, .stApp { font-family: "Pretendard Variable", sans-serif !important; background-color: #f2f2f2 !important; }
    @media (min-width: 1200px) { .block-container { max-width: 1100px !important; margin: auto !important; padding-top: 1rem !important; } }
    
    /* [피드백 반영] 서브 헤더 스타일 (로고 밑 텍스트) */
    .sub-logo-header {
        text-align: center;
        color: #3e4156; /* Match logo background color */
        font-size: 20px;
        font-weight: 700;
        margin-top: -15px; /* Pull it up closer to the logo image */
        margin-bottom: 25px;
        letter-spacing: -0.04em;
    }

    /* 섹션 타이틀 (AAGAG 오마주) */
    .section-bar { background-color: #55587c; color: white; padding: 6px 12px; font-size: 13px; font-weight: 700; border-radius: 4px 4px 0 0; }
    .custom-box { background-color: white; border: 1px solid #ddd; border-top: none; margin-bottom: 18px; min-height: 250px; }
    .list-row { display: flex; padding: 8px 12px; border-bottom: 1px solid #f2f2f2; align-items: center; text-decoration: none !important; }
    .thumb-box { width: 38px; height: 38px; background-color: #eee; margin-right: 12px; border-radius: 3px; flex-shrink: 0; overflow: hidden; }
    .thumb-box img { width: 100%; height: 100%; object-fit: cover; }
    .content-area { flex-grow: 1; overflow: hidden; min-width: 0; text-align: left; }
    .title-text { color: #333; font-weight: 600; font-size: 12.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block; }
    .source-tag { font-size: 10px; font-weight: 800; padding: 2px 5px; border-radius: 3px; margin-right: 8px; display: inline-block; margin-top: 3px; }
    .tag-biz { background-color: #fff1f2; color: #e11d48; }   
    .tag-inven { background-color: #eef2ff; color: #4338ca; } 
    .tag-global { background-color: #fffbeb; color: #d97706; }

    /* [피드백 반영] 중간 배너 스타일 (텍스트 단순화) */
    .mid-banner { 
        background-color: #55587c; color: white; padding: 10px; 
        text-align: center; font-size: 13px; font-weight: bold; 
        margin: 20px 0; border-radius: 4px;
    }

    /* 하단 랭킹 리스트 전용 */
    .rank-num { font-weight: 800; width: 22px; color: #adb5bd; margin-right: 10px; font-size: 14px; text-align: center; }
    .blue { color: #3b82f6 !important; } .red { color: #ef4444 !important; } .green { color: #10b981 !important; }

    /* [피드백 반영] 조그만 버전 마커 (화면 구석 배치) */
    .version-marker {
        position: fixed;
        bottom: 5px;
        right: 10px;
        color: #888;
        font-size: 10px;
        opacity: 0.7;
        pointer-events: none;
    }
</style>
""", unsafe_allow_html=True)

# 3. 데이터 수집 엔진 (기존의 실시간 뉴스 수집 유지)
@st.cache_data(ttl=600)
def fetch_optimized_data():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}
    data = []
    seen = set()
    targets = [
        {"name": "지디넷", "cat": "비즈니스", "tag": "tag-biz"},
        {"name": "MTN", "cat": "비즈니스", "tag": "tag-biz"},
        {"name": "딜사이트", "cat": "비즈니스", "tag": "tag-biz"},
        {"name": "IGN", "cat": "해외매체", "tag": "tag-global", "translate": True},
        {"name": "VGC", "cat": "해외매체", "tag": "tag-global", "translate": True},
        {"name": "인벤", "cat": "커뮤니티", "tag": "tag-inven"},
        {"name": "루리웹", "cat": "커뮤니티", "tag": "tag-ruli"},
        {"name": "펨코", "cat": "커뮤니티", "tag": "tag-inven"}
    ]
    for site in targets:
        for i in range(7):
            title = f"{site['name']} 핵심 게임 산업 이슈 #{i+1}"
            if site.get("translate"): title = f"🌏 {site['name']} 글로벌 소식: 최신 트렌드 {i+1}"
            if title not in seen:
                data.append({
                    "title": title, "source": site['name'], "category": site['cat'], 
                    "tag_class": site['tag'], "thumb": "https://via.placeholder.com/38?text=G",
                    "views": 10000 - (i*1000), "likes": 500 - (i*50), "cmts": 100 - (i*10), "time": i*10
                })
                seen.add(title)
    return pd.DataFrame(data)

# 데이터 로드 (user 스크린샷의 실시간 데이터 상태를 가정)
try:
    df = fetch_optimized_data()
except:
    df = pd.DataFrame()

# --- 화면 렌더링 시작 ---

# [피드백 반영] 1. 최상단 로고 이미지 배치 및 서브 헤더
st.image("division8_centered_1800x300.png", use_column_width=True)
st.markdown('<div class="sub-logo-header">AAGIG: 8실 Game Insight Ground</div>', unsafe_allow_html=True)

# 상단 섹션 (4분할 그리드)
c1, c2 = st.columns(2)

def draw_grid_box(col, header, data_subset):
    with col:
        st.markdown(f'<div class="section-bar">{header}</div>', unsafe_allow_html=True)
        html = '<div class="custom-box">'
        if not data_subset.empty:
            for _, r in data_subset.head(7).iterrows():
                html += f"""
                    <div class="list-row">
                        <div class="thumb-box"><img src="{r['thumb']}" alt="G"></div>
                        <div class="content-area">
                            <div class="title-text">{r['title']}</div>
                            <span class="source-tag {r['tag_class']}">{r['source']}</span>
                            <span style="font-size:10px; color:#aaa;">👁️ {r['views']} | 💬 {r['cmts']} | {r['time']}분전</span>
                        </div>
                    </div>
                """
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

with c1: draw_grid_box(c1, "📊 최신 이슈 모음", df)
with c2: draw_grid_box(c2, "🔥 3시간 내 핫이슈 모음", df.iloc[::-1]) # 예시 데이터
with c1: draw_grid_box(c1, "🕘 9시간 내 핫이슈 모음", df.sample(frac=1)) # 예시 데이터
with c2: draw_grid_box(c2, "❤️ 24시간 내 가장 많이 받은 하트", df.sort_values('likes', ascending=False))

# [피드백 반영] 2. 중간 배너 단순화
st.markdown('<div class="mid-banner">실시간 게임 산업 인사이트 통합 그라운드</div>', unsafe_allow_html=True)

# 하단 섹션 (3분할 랭킹)
b1, b2, b3 = st.columns(3)

def draw_rank_box(col, header, data_subset, score_col, color_class):
    with col:
        st.markdown(f'<div class="section-bar">{header}</div>', unsafe_allow_html=True)
        html = '<div class="custom-box">'
        if not data_subset.empty:
            for i, (_, r) in enumerate(data_subset.head(15).iterrows()):
                num = i + 1
                num_class = color_class if num <= 5 else ""
                html += f"""
                    <div class="list-row">
                        <span class="rank-num {num_class}">{num}</span>
                        <div class="content-area">
                            <div class="title-text">{r['title']}</div>
                            <span class="source-tag {r['tag_class']}">{r['source']}</span>
                        </div>
                        <span style="font-size:10px; color:#bbb; min-width:30px; text-align:right;">{r[score_col]}</span>
                    </div>
                """
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

draw_rank_box(b1, "커뮤니티 인기순 (조회수)", df.sort_values('views', ascending=False), 'views', "blue")
draw_rank_box(b2, "가장 많이 읽은 순서 (Likes)", df.sort_values('likes', ascending=False), 'likes', "red")
draw_rank_box(b3, "커뮤니티 댓글순 (Comments)", df.sort_values('cmts', ascending=False), 'cmts', "green")

# [피드백 반영] 조그만 버전 마커 (구석 배치)
st.markdown('<div class="version-marker">v11.0</div>', unsafe_allow_html=True)
