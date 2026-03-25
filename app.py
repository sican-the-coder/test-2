import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

# 1. 페이지 설정
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

# 2. 스타일 시트 (v12.0 디자인 100% 영구 박제)
st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
<style>
    body, .stApp { font-family: "Pretendard Variable", sans-serif !important; background-color: #f2f2f2 !important; }
    @media (min-width: 1200px) { .block-container { max-width: 1100px !important; margin: auto !important; padding-top: 1.5rem !important; } }
    
    .sub-logo-header { text-align: center; color: #3e4156; font-size: 20px; font-weight: 700; margin-top: 5px; margin-bottom: 25px; letter-spacing: -0.04em; }
    .section-bar { background-color: #55587c; color: white; padding: 6px 12px; font-size: 13px; font-weight: 700; border-radius: 4px 4px 0 0; }
    .custom-box { background-color: white; border: 1px solid #ddd; border-top: none; margin-bottom: 18px; min-height: 280px; }
    
    .list-row { display: flex; padding: 8px 12px; border-bottom: 1px solid #f2f2f2; align-items: center; text-decoration: none !important; }
    .thumb-box { width: 38px; height: 38px; background-color: #eee; margin-right: 12px; border-radius: 3px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; overflow: hidden; }
    .thumb-box img { width: 100%; height: 100%; object-fit: cover; }
    
    .content-area { flex-grow: 1; overflow: hidden; min-width: 0; text-align: left; }
    
    /* [핵심] 제목 클릭 가능하지만 v12.0처럼 검은색 평문으로 보이게 고정 */
    .title-text { color: #333 !important; font-weight: 600; font-size: 12.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block; text-decoration: none !important; }
    .title-text:hover { color: #3b82f6 !important; text-decoration: underline !important; }

    .source-tag { font-size: 10px; font-weight: 800; padding: 2px 5px; border-radius: 3px; margin-right: 8px; display: inline-block; margin-top: 3px; }
    
    .tag-biz { background-color: #fff1f2; color: #e11d48; }   
    .tag-inven { background-color: #eef2ff; color: #4338ca; } 
    .tag-mtn { background-color: #f0fdf4; color: #166534; }
    .tag-ds { background-color: #fef2f2; color: #991b1b; }
    .tag-zd { background-color: #fffbeb; color: #b45309; }
    
    .mid-banner { background-color: #55587c; color: white; padding: 10px; text-align: center; font-size: 13px; font-weight: bold; margin: 15px 0; border-radius: 4px; }
    .rank-num { font-weight: 800; width: 22px; color: #adb5bd; margin-right: 10px; font-size: 14px; text-align: center; }
    .blue { color: #3b82f6 !important; } .red { color: #ef4444 !important; } .green { color: #10b981 !important; }
    .version-marker { position: fixed; bottom: 5px; right: 10px; color: #888; font-size: 10px; opacity: 0.5; pointer-events: none; }
</style>
""", unsafe_allow_html=True)

# 3. [안전 장치 추가] 통합 데이터 수집 엔진
@st.cache_data(ttl=300)
def fetch_integrated_data():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    results = []
    seen = set()

    # 1. 네이버 게임 뉴스 (가장 안정적인 기본 소스)
    try:
        r = requests.get("https://news.naver.com/section/105", headers=headers, timeout=3)
        soup = BeautifulSoup(r.text, 'html.parser')
        for art in soup.select('.sa_item'):
            title_el = art.select_one('.sa_text_title, .sa_text_strong')
            link_el = art.select_one('a')
            if title_el and link_el:
                title = title_el.get_text(strip=True)
                if ('게임' in title or '넥슨' in title or '엔씨' in title) and title not in seen:
                    press = art.select_one('.sa_text_press').get_text(strip=True) if art.select_one('.sa_text_press') else "네이버"
                    img = art.select_one('img')
                    results.append({"title": title, "link": link_el['href'], "source": press, "tag": "tag-biz", "thumb": img.get('data-src') or img.get('src') or "" if img else "", "views": "1.2k", "cmts": "14"})
                    seen.add(title)
    except: pass

    # 2. 지디넷 코리아 (요청 링크)
    try:
        r = requests.get("https://zdnet.co.kr/news/?lstcode=0060&page=2", headers=headers, timeout=3)
        soup = BeautifulSoup(r.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            if '/view/?no=' in a['href']:
                title = a.get_text(strip=True)
                if len(title) > 10 and title not in seen:
                    link = "https://zdnet.co.kr" + a['href'] if not a['href'].startswith('http') else a['href']
                    results.append({"title": title, "link": link, "source": "지디넷", "tag": "tag-zd", "thumb": "", "views": "2.8k", "cmts": "32"})
                    seen.add(title)
    except: pass

    # 3. 딜사이트 넥슨 검색 (요청 링크)
    try:
        r = requests.get("https://dealsite.co.kr/search/?LIKE=%EB%84%A5%EC%8A%A8&SEARCHFIELD=TITLE_CONTENT", headers=headers, timeout=3)
        soup = BeautifulSoup(r.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            if '/articles/' in a['href']:
                title = a.get_text(strip=True)
                if len(title) > 10 and title not in seen:
                    link = "https://dealsite.co.kr" + a['href']
                    results.append({"title": title, "link": link, "source": "딜사이트", "tag": "tag-ds", "thumb": "", "views": "1.5k", "cmts": "0"})
                    seen.add(title)
    except: pass

    # 4. MTN 서정근 검색 (요청 링크)
    try:
        r = requests.get("https://news.mtn.co.kr/search/%EC%84%9C%EC%A0%95%EA%B7%BC", headers=headers, timeout=3)
        soup = BeautifulSoup(r.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            if 'v=' in a['href'] or 'news-detail' in a['href']:
                title = a.get_text(strip=True)
                if len(title) > 10 and title not in seen:
                    link =
