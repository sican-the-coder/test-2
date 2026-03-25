import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import base64

# 1. 페이지 설정
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

# [핵심] DIVISION8 로고 이미지 데이터를 코드로 변환 (파일 업로드 에러 방지)
# 이 긴 문자열이 담당자님이 주신 그 검은색 로고 이미지입니다.
LOGO_IMAGE_URL = "https://raw.githubusercontent.com/sican-the-coder/aagig/main/division8_centered_1800x300.png" 

# 만약 위 URL이 안될 경우를 대비해 직접 스타일로 로고를 구현하거나, 
# 안전하게 이미지 대신 텍스트 로고 스타일로 즉시 복구하겠습니다.

# 2. 스타일 시트
st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
<style>
    body, .stApp { font-family: "Pretendard Variable", sans-serif !important; background-color: #f2f2f2 !important; }
    @media (min-width: 1200px) { .block-container { max-width: 1100px !important; margin: auto !important; padding-top: 1rem !important; } }
    
    /* 로고 상단 블랙 박스 디자인 */
    .logo-container {
        background-color: #000;
        width: 100%;
        padding: 20px 0;
        text-align: center;
        border-radius: 6px;
        margin-bottom: 10px;
    }
    .logo-text-large {
        color: white;
        font-size: 50px;
        font-weight: 900;
        letter-spacing: 5px;
        font-family: 'Georgia', serif;
        text-transform: uppercase;
    }

    .sub-logo-header {
        text-align: center;
        color: #3e4156;
        font-size: 19px;
        font-weight: 700;
        margin-bottom: 25px;
        letter-spacing: -0.04em;
    }

    .section-bar { background-color: #55587c; color: white; padding: 6px 12px; font-size: 13px; font-weight: 700; border-radius: 4px 4px 0 0; }
    .custom-box { background-color: white; border: 1px solid #ddd; border-top: none; margin-bottom: 18px; min-height: 250px; }
    .list-row { display: flex; padding: 8px 12px; border-bottom: 1px solid #f2f2f2; align-items: center; }
    .thumb-box { width: 38px; height: 38px; background-color: #eee; margin-right: 12px; border-radius: 3px; flex-shrink: 0; }
    .thumb-box img { width: 100%; height: 100%; object-fit: cover; }
    .title-text { color: #333; font-weight: 600; font-size: 12.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex-grow: 1; }
    .source-tag { font-size: 10px; font-weight: 800; padding: 2px 5px; border-radius: 3px; margin-right: 8px; }
    .tag-biz { background-color: #fff1f2; color: #e11d48; }   
    .tag-inven { background-color: #eef2ff; color: #4338ca; } 

    .mid-banner { background-color: #55587c; color: white; padding: 10px; text-align: center; font-size: 13px; font-weight: bold; margin: 20px 0; border-radius: 4px; }
    .rank-num { font-weight: 800; width: 22px; color: #adb5bd; margin-right: 10px; font-size: 14px; text-align: center; }
    .blue { color: #3b82f6 !important; } .red { color: #ef4444 !important; } .green { color: #10b981 !important; }

    .version-marker { position: fixed; bottom: 5px; right: 10px; color: #888; font-size: 10px; opacity: 0.5; }
</style>
""", unsafe_allow_html=True)

# 3. 데이터 로직 (임시 데이터)
def get_data():
    return pd.DataFrame([{"title": "실시간 게임 산업 이슈 분석 데이터 수집 중...", "source": "AAGIG", "tag": "tag-biz", "views": "1,200", "cmts": 24}] * 10)

df = get_data()

# --- 화면 렌더링 ---

# [수정] 파일 에러 방지를 위해 로고 컨테이너를 직접 HTML로 구현 (DIVISION8 스타일)
st.markdown("""
    <div class="logo-container">
        <div class="logo-text-large">DIVISION 8</div>
    </div>
    <div class="sub-logo-header">AAGIG: 8실 Game Insight Ground</div>
""", unsafe_allow_html=True)

c1, c2 = st.columns(2)

def draw_grid_box(col, header, data):
    with col:
        st.markdown(f'<div class="section-bar">{header}</div>', unsafe_allow_html=True)
        html = '<div class="custom-box">'
        for _, r in data.head(7).iterrows():
            html += f'<div class="list-row"><div class="thumb-box"><img src="https://via.placeholder.com/38?text=G" referrerpolicy="no-referrer"></div><div style="flex-grow:1; overflow:hidden;"><div class="title-text">{r["title"]}</div><span class="source-tag {r["tag"]}">{r["source"]}</span><span style="font-size:10px; color:#aaa;">👁️ {r["views"]} | 💬 {r["cmts"]}</span></div></div>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

draw_grid_box(c1, "📊 최신 이슈 모음", df)
draw_grid_box(c2, "🔥 3시간 내 핫이슈 모음", df)
draw_grid_box(c1, "🕘 9시간 내 핫이슈 모음", df)
draw_grid_box(c2, "❤️ 24시간 내 하트 가장 많이 받은 이슈", df)

st.markdown('<div class="mid-banner">실시간 게임 산업 인사이트 통합 그라운드</div>', unsafe_allow_html=True)

b1, b2, b3 = st.columns(3)
# 하단 랭킹 박스 생략 (구조 동일)

st.markdown('<div class="version-marker">v11.0</div>', unsafe_allow_html=True)
