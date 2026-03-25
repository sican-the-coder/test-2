import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

# 1. 페이지 설정
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

# 2. 스타일 설정 (깨짐 방지용 정교한 CSS)
st.markdown("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
    <style>
    body, .stApp { font-family: "Pretendard Variable", sans-serif !important; background-color: #f2f2f2; }
    @media (min-width: 1200px) { .block-container { max-width: 1100px !important; margin: auto; } }
    
    /* 섹션 바 디자인 */
    .section-bar { 
        background-color: #55587c; color: white; padding: 8px 12px; 
        font-size: 13px; font-weight: 700; border-radius: 4px 4px 0 0; margin-top: 10px;
    }
    
    /* 리스트 박스 내부 디자인 */
    .custom-container { 
        background-color: white; border: 1px solid #ddd; border-top: none; 
        padding: 5px 0; margin-bottom: 20px; min-height: 300px;
    }
    .list-item { 
        display: flex; padding: 8px 15px; border-bottom: 1px solid #f2f2f2; 
        font-size: 12.5px; align-items: center; 
    }
    .tag-source { color: #4338ca; font-weight: 800; min-width: 60px; font-size: 11px; }
    .title-text { color: #333; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    
    /* 타이틀 바 */
    .main-logo-bar { background-color: #3e4156; padding: 15px; color: white; border-radius: 6px; margin-bottom: 10px; font-weight: 800; font-size: 22px; text-align: center;}
    </style>
""", unsafe_allow_html=True)

# 3. 데이터 수집 (중복 제거 로직 추가)
def fetch_final_data():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}
    results = []
    seen_titles = set() # 중복 체크용 집합

    # [수집 1] 네이버 IT (비즈니스용)
    try:
        res = requests.get("https://news.naver.com/section/105", headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        news_items = soup.select('.sa_text_title, .sa_text_strong')
        for item in news_items:
            title = item.get_text(strip=True)
            if title not in seen_titles: # 중복이 아니면 추가
                results.append({"title": title, "source": "뉴스", "category": "비즈니스"})
                seen_titles.add(title)
    except: pass

    # [수집 2] 인벤 최신 뉴스 (커뮤니티용)
    try:
        res = requests.get("https://www.inven.co.kr/webzine/news/", headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        inven_items = soup.select('.newsList .info .title')
        for item in inven_items:
            title = item.get_text(strip=True)
            if title not in seen_titles:
                results.append({"title": title, "source": "인벤", "category": "커뮤니티"})
                seen_titles.add(title)
    except: pass

    # 비상용 가상 데이터 (수집 실패 시 리스트가 비지 않도록 채움)
    if len(results) < 5:
        samples = [
            {"title": "지디넷: [단독] K-게임 상반기 신작 라인업 공개", "source": "지디넷", "category": "비즈니스"},
            {"title": "MTN: 게임주, 실적 발표 앞두고 기대감 상승", "source": "MTN", "category": "비즈니스"},
            {"title": "루리웹: '스텔라 블레이드' 개발진 인터뷰 공개", "source": "루리웹", "category": "커뮤니티"},
            {"title": "펨코: 이번 주 게임 업데이트 총정리 (베스트)", "source": "펨코", "category": "커뮤니티"}
        ]
        results.extend(samples)

    return pd.DataFrame(results)

df = fetch_final_data()

# --- 화면 렌더링 ---
st.markdown('<div class="main-logo-bar">AAGIG: Game Insight Ground</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)

# 섹션 1: 비즈니스/IT
with c1:
    st.markdown('<div class="section-bar">📉 비즈니스/IT (지디넷, MTN, 딜사이트 등)</div>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="custom-container">', unsafe_allow_html=True)
        biz_df = df[df['category'] == '비즈니스']
        for _, r in biz_df.head(10).iterrows():
            st.markdown(f'<div class="list-item"><span class="tag-source">{r["source"]}</span><span class="title-text">{r["title"]}</span></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# 섹션 2: 커뮤니티
with c2:
    st.markdown('<div class="section-bar">🔥 국내 커뮤니티 (인벤, 루리웹, 펨코)</div>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="custom-container">', unsafe_allow_html=True)
        comm_df = df[df['category'] == '커뮤니티']
        for _, r in comm_df.head(10).iterrows():
            st.markdown(f'<div class="list-item"><span class="tag-source">{r["source"]}</span><span class="title-text">{r["title"]}</span></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
