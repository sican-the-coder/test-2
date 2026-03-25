import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import hashlib
import re

# 1. 페이지 설정
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

# 2. 스타일 시트 (v12.0 디자인 100% 영구 박제 + [6] 제목 줄바꿈 추가)
st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
<style>
    body, .stApp { font-family: "Pretendard Variable", sans-serif !important; background-color: #f2f2f2 !important; }
    @media (min-width: 1200px) { .block-container { max-width: 1100px !important; margin: auto !important; padding-top: 1.5rem !important; } }
    .sub-logo-header { text-align: center; color: #3e4156; font-size: 20px; font-weight: 700; margin-top: 5px; margin-bottom: 25px; letter-spacing: -0.04em; }
    .section-bar { background-color: #55587c; color: white; padding: 6px 12px; font-size: 13px; font-weight: 700; border-radius: 4px 4px 0 0; display: flex; justify-content: space-between; align-items: center; }
    .custom-box { background-color: white; border: 1px solid #ddd; border-top: none; margin-bottom: 18px; min-height: 280px; }
    .list-row { display: flex; padding: 8px 12px; border-bottom: 1px solid #f2f2f2; align-items: center; text-decoration: none !important; }
    
    /* [3] 썸네일 박스 복구 */
    .thumb-box { width: 38px; height: 38px; background-color: #eee; margin-right: 12px; border-radius: 3px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; overflow: hidden; }
    .thumb-box img { width: 100%; height: 100%; object-fit: cover; }
    .content-area { flex-grow: 1; overflow: hidden; min-width: 0; text-align: left; }
    
    /* [6] 제목 줄바꿈 적용 (v12.0 폰트 유지) */
    .title-link { color: #333 !important; font-weight: 600; font-size: 12.5px; text-decoration: none !important; display: block; line-height: 1.4; word-break: keep-all; }
    .title-link:hover { color: #3b82f6 !important; text-decoration: underline !important; }

    .source-tag { font-size: 10px; font-weight: 800; padding: 2px 5px; border-radius: 3px; margin-right: 8px; display: inline-block; margin-top: 3px; }
    .tag-biz { background-color: #fff1f2; color: #e11d48; }   
    .tag-inven { background-color: #eef2ff; color: #4338ca; } 
    .tag-global { background-color: #fffbeb; color: #d97706; }
    .mid-banner { background-color: #55587c; color: white; padding: 10px; text-align: center; font-size: 13px; font-weight: bold; margin: 15px 0; border-radius: 4px; }
    .version-marker { position: fixed; bottom: 5px; right: 10px; color: #888; font-size: 10px; opacity: 0.5; pointer-events: none; }
</style>
""", unsafe_allow_html=True)

# [5] 영어 글 제목 번역기 (간이 엔진)
def translate_title(text):
    if not re.search('[가-힣]', text):
        trans_map = {"Release Date": "출시일", "Review": "리뷰", "Update": "업데이트", "New": "신규", "Game": "게임"}
        for k, v in trans_map.items(): text = text.replace(k, v)
        return "🌏 [국방번역] " + text
    return text

# 4. 통합 데이터 엔진 (피드백 반영)
@st.cache_data(ttl=300)
def fetch_all_data():
    headers = {"User-Agent": "Mozilla/5.0"}
    res = []
    seen = set()

    # 데이터 소스들 (네이버, 인벤, 루리웹, 지디넷, 딜사이트, MTN, IGN)
    urls = [
        ("네이버", "https://news.naver.com/section/105", "tag-biz"),
        ("인벤", "https://www.inven.co.kr/webzine/news/", "tag-inven"),
        ("IGN", "https://www.ign.com/news", "tag-global"),
        ("지디넷", "https://zdnet.co.kr/news/?lstcode=0060", "tag-biz"),
        ("딜사이트", "https://dealsite.co.kr/search/?LIKE=%EB%84%A5%EC%8A%A8&SEARCHFIELD=TITLE", "tag-biz")
    ]
    
    for source_name, url, tag in urls:
        try:
            r = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(r.text, 'html.parser')
            # 매체별 기사 추출 (간략화)
            for art in soup.select('.sa_item, .newsList li, .content-item, .news_item, .title')[:10]:
                title_el = art.select_one('.sa_text_title, .title, .item-title, .subject, a')
                if title_el:
                    title = title_el.get_text(strip=True)
                    if title not in seen and len(title) > 5:
                        link = art.select_one('a')['href']
                        if not link.startswith('http'): link = (url.split('/')[0] + "//" + url.split('/')[2] + link)
                        img = art.select_one('img')
                        thumb = img.get('data-src') or img.get('src') or "" if img else ""
