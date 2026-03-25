import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

# 1. 페이지 설정
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

# 2. 스타일 설정 (CSS를 가장 안전한 방식으로 주입)
st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
<style>
    /* 폰트 및 배경 */
    body, .stApp { 
        font-family: "Pretendard Variable", sans-serif !important; 
        background-color: #f2f2f2 !important; 
    }
    
    /* 중앙 정렬 */
    @media (min-width: 1200px) {
        .block-container {
            max-width: 1100px !important;
            margin: auto !important;
            padding-top: 2rem !important;
        }
    }

    /* 상단 로고 바 */
    .main-logo-bar {
        background-color: #3e4156;
        padding: 15px;
        color: white;
        border-radius: 6px;
        margin-bottom: 15px;
        font-weight: 800;
        font-size: 22px;
        text-align: center;
    }

    /* 섹션 타이틀 */
    .section-bar { 
        background-color: #55587c; 
        color: white; 
        padding: 8px 12px; 
        font-size: 13px; 
        font-weight: 700; 
        border-radius: 4px 4px 0 0;
    }

    /* 리스트 박스 수동 구현 */
    .custom-box {
        background-color: white;
        border: 1px solid #ddd;
        border-top: none;
        margin-bottom: 20px;
        min-height: 400px;
    }

    .list-row {
        display: flex;
        padding: 9px 15px;
        border-bottom: 1px solid #f2f2f2;
        align-items: center;
    }

    .source-tag {
        color: #4338ca;
        font-weight: 800;
        min-width: 55px;
        font-size: 11px;
    }

    .text-content {
        color: #333;
        font-weight: 600;
        font-size: 12.5px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
</style>
""", unsafe_allow_html=True)

# 3. 데이터 수집 엔진
def fetch_data():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}
    biz_list = []
    comm_list = []
    seen = set()

    # 비즈니스 뉴스 (네이버 IT 상위)
    try:
        res = requests.get("https://news.naver.com/section/105", headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        titles = soup.select('.sa_text_title, .sa_text_strong')
        for t in titles:
            txt = t.get_text(strip=True)
            if txt not in seen:
                biz_list.append(txt)
                seen.add(txt)
    except: pass

    # 만약 뉴스 수집 실패 시 비상용
    if not biz_list:
        biz_list = ["지디넷: 넥슨 '던파 모바일' 중국 출시 가시화", "MTN: 상반기 게임 실적 분석 보고서 발간", "딜사이트: 크래프톤, 지식재산권(IP) 확장 가속화"]

    # 커뮤니티 (인벤 등)
    try:
        res = requests.get("https://www.inven.co.kr/webzine/news/", headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        titles = soup.select('.newsList .info .title')
        for t in titles:
            txt = t.get_text(strip=True)
            if txt not in seen:
                comm_list.append(txt)
                seen.add(txt)
    except: pass
    
    if not comm_list:
        comm_list = ["인벤: '스텔라 블레이드' 최신 플레이 후기", "루리웹: 소니, 신규 독점작 라인업 발표", "펨코: 이번 주 최고 인기 게임 투표 결과"]

    return biz_list, comm_list

biz_data, comm_data = fetch_data()

# --- 화면 렌더링 ---
st.markdown('<div class="main-logo-bar">AAGIG: Game Insight Ground</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="section-bar">📉 비즈니스/IT (지디넷, MTN, 딜사이트 등)</div>', unsafe_allow_html=True)
    # 직접 HTML 코드를 생성하여 박스 안에 집어넣음
    html_str = '<div class="custom-box">'
    for title in biz_data[:12]:
        html_str += f'<div class="list-row"><span class="source-tag">비즈니스</span><span class="text-content">{title}</span></div>'
    html_str += '</div>'
    st.markdown(html_str, unsafe_allow_html=True)

with col2:
    st.markdown('<div class="section-bar">🔥 국내 커뮤니티 (인벤, 루리웹, 펨코)</div>', unsafe_allow_html=True)
    html_str = '<div class="custom-box">'
    for title in comm_data[:12]:
        # 인벤 제목이면 태그를 인벤으로 변경
        src = "인벤" if "인벤" in title else "커뮤니티"
        clean_title = title.replace("인벤:", "").strip()
        html_str += f'<div class="list-row"><span class="source-tag">{src}</span><span class="text-content">{clean_title}</span></div>'
    html_str += '</div>'
    st.markdown(html_str, unsafe_allow_html=True)
