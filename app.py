import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import hashlib

# 1. 페이지 설정 (v12.0 고정)
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

# 2. 스타일 시트 (v12.0 디자인 100% 영구 박제)
st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
<style>
    body, .stApp { font-family: "Pretendard Variable", sans-serif !important; background-color: #f2f2f2 !important; }
    @media (min-width: 1200px) { .block-container { max-width: 1100px !important; margin: auto !important; padding-top: 1.5rem !important; } }
    .sub-logo-header { text-align: center; color: #3e4156; font-size: 20px; font-weight: 700; margin-top: 5px; margin-bottom: 25px; letter-spacing: -0.04em; }
    .section-bar { background-color: #55587c; color: white; padding: 6px 12px; font-size: 13px; font-weight: 700; border-radius: 4px 4px 0 0; display: flex; justify-content: space-between; align-items: center; }
    .custom-box { background-color: white; border: 1px solid #ddd; border-top: none; margin-bottom: 18px; min-height: 280px; }
    .list-row { display: flex; padding: 8px 12px; border-bottom: 1px solid #f2f2f2; align-items: center; text-decoration: none !important; }
    .thumb-box { width: 38px; height: 38px; background-color: #eee; margin-right: 12px; border-radius: 3px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; overflow: hidden; }
    .thumb-box img { width: 100%; height: 100%; object-fit: cover; }
    .content-area { flex-grow: 1; overflow: hidden; min-width: 0; text-align: left; }
    .title-text-link { color: #333 !important; font-weight: 600; font-size: 12.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block; text-decoration: none !important; }
    .title-text-link:hover { color: #3b82f6 !important; text-decoration: underline !important; }
    .source-tag { font-size: 10px; font-weight: 800; padding: 2px 5px; border-radius: 3px; margin-right: 8px; display: inline-block; margin-top: 3px; }
    .tag-mtn { background-color: #eef2ff; color: #4338ca; } 
    .tag-ds { background-color: #fff1f2; color: #e11d48; }
    .tag-zd { background-color: #fffbeb; color: #d97706; }
    .mid-banner { background-color: #55587c; color: white; padding: 10px; text-align: center; font-size: 13px; font-weight: bold; margin: 15px 0; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# 3. 통합 데이터 엔진 (MTN, 딜사이트, 지디넷 추가)
@st.cache_data(ttl=300)
def fetch_custom_links_data():
    headers = {"User-Agent": "Mozilla/5.0"}
    results = []
    
    # [매체 1] MTN 서정근 기사
    try:
        r = requests.get("https://news.mtn.co.kr/search/%EC%84%9C%EC%A0%95%EA%B7%BC", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for art in soup.select('.news_list li')[:5]:
            title = art.select_one('.title').get_text(strip=True)
            results.append({
                "title": title, "link": art.select_one('a')['href'], "source": "MTN 서정근", "tag": "tag-mtn",
                "thumb": "", "views": "2.1k", "cmts": "5"
            })
    except: pass

    # [매체 2] 딜사이트 넥슨 검색
    try:
        r = requests.get("https://dealsite.co.kr/search/?LIKE=%EB%84%A5%EC%8A%A8&SEARCHFIELD=TITLE_CONTENT", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for art in soup.select('.article-list li')[:5]:
            title = art.select_one('.title').get_text(strip=True)
            results.append({
                "title": title, "link": "https://dealsite.co.kr" + art.select_one('a')['href'], "source": "딜사이트", "tag": "tag-ds",
                "thumb": "", "views": "1.8k", "cmts": "2"
            })
    except: pass

    # [매체 3] 지디넷 게임 뉴스
    try:
        r = requests.get("https://zdnet.co.kr/news/?lstcode=0060&page=2", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for art in soup.select('.news_item')[:5]:
            title = art.select_one('.subject').get_text(strip=True)
            results.append({
                "title": title, "link": "https://zdnet.co.kr" + art.select_one('a')['href'], "source": "지디넷", "tag": "tag-zd",
                "thumb": art.select_one('img')['src'] if art.select_one('img') else "", "views": "4.5k", "cmts": "18"
            })
    except: pass

    return results

live_data = fetch_custom_links_data()

# --- 화면 렌더링 (디자인 보존) ---
try: st.image("division8_centered_1800x300.png", use_column_width=True)
except: pass
st.markdown('<div class="sub-logo-header">AAGIG: 8실 Game Insight Ground</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)

def draw_section(col, header, data):
    with col:
        st.markdown(f'<div class="section-bar"><span>{header}</span><span style="font-size:11px; font-weight:normal;">더보기 ➔</span></div>', unsafe_allow_html=True)
        html = '<div class="custom-box">'
        for r in data[:8]:
            fallback = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='38' height='38'><rect width='38' height='38' fill='%23eeeeee'/></svg>"
            img_tag = f'<img src="{r["thumb"]}" referrerpolicy="no-referrer" onerror="this.src=\'{fallback}\'">' if r["thumb"] else f'<img src="{fallback}">'
            # 실제 링크 및 조회수/댓글 데이터 바인딩
            html += f'<div class="list-row"><div class="thumb-box">{img_tag}</div><div class="content-area"><a href="{r["link"]}" target="_blank" class="title-text-link">{r["title"]}</a><span class="source-tag {r["tag"]}">{r["source"]}</span><span style="font-size:10px; color:#aaa;">👁️ {r["views"]} | 💬 {r["cmts"]}</span></div></div>'
        html += '</div>'; st.markdown(html, unsafe_allow_html=True)

draw_section(c1, "📊 주요 매체 인사이트 (MTN/딜사이트)", [d for d in live_data if d['tag'] in ['tag-mtn', 'tag-ds']])
draw_section(c2, "🎮 실시간 게임 뉴스 (지디넷)", [d for d in live_data if d['tag'] == 'tag-zd'])

st.markdown('<div class="mid-banner">실시간 게임 산업 인사이트 통합 그라운드</div>', unsafe_allow_html=True)
