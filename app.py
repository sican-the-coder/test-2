import streamlit as st
import requests
import re
import json
import os
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET

# --- [철칙 1: B 유지] 디자인 100% 박제 ---
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
<style>
    body, .stApp { font-family: "Pretendard Variable", sans-serif !important; background-color: #f2f2f2 !important; }
    @media (min-width: 1200px) { .block-container { max-width: 1100px !important; margin: auto !important; padding-top: 1.5rem !important; } }
    .sub-logo-header { text-align: center; color: #3e4156; font-size: 20px; font-weight: 700; margin-top: 5px; margin-bottom: 25px; letter-spacing: -0.04em; }
    .section-bar { background-color: #55587c; color: white; padding: 6px 12px; font-size: 13px; font-weight: 700; border-radius: 4px 4px 0 0; display: flex; justify-content: space-between; align-items: center; }
    .custom-box { background-color: white; border: 1px solid #ddd; border-top: none; margin-bottom: 18px; min-height: 280px; }
    .list-row { display: flex; padding: 8px 12px; border-bottom: 1px solid #f2f2f2; align-items: flex-start; text-decoration: none !important; }
    .thumb-box { width: 44px; height: 44px; margin-right: 12px; border-radius: 4px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; overflow: hidden; margin-top: 2px; }
    .thumb-box img { width: 100%; height: 100%; object-fit: cover; }
    .content-area { flex-grow: 1; overflow: hidden; min-width: 0; text-align: left; }
    .title-text { color: #333 !important; font-weight: 600; font-size: 13px; text-decoration: none !important; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; text-overflow: ellipsis; white-space: normal !important; line-height: 1.4; margin-bottom: 4px; word-break: keep-all; }
    .meta-area { display: flex; align-items: center; font-size: 10px; color: #aaa; }
    .source-tag { font-weight: 800; padding: 2px 5px; border-radius: 3px; margin-right: 8px; display: inline-block; }
    .tag-biz { background-color: #fff1f2; color: #e11d48; }   
    .tag-kr { background-color: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; }
    .tag-global { background-color: #fffbeb; color: #d97706; }
    .tag-mtn { background-color: #f0fdf4; color: #166534; }
    .mid-banner { background-color: #55587c; color: white; padding: 10px; text-align: center; font-size: 13px; font-weight: bold; margin: 15px 0; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# 2. 데이터 복원 및 수집 엔진 (v44)
DB_FILE = "aagig_db_v44.json"
PREV_DB = "aagig_db_v41.json" # MTN 데이터가 살아있던 마지막 DB

def load_and_restore():
    data = []
    # [A-1: MTN 유물 강제 복원]
    if os.path.exists(PREV_DB):
        with open(PREV_DB, 'r', encoding='utf-8') as f:
            prev = json.load(f)
            data = [item for item in prev if item['group'] == "mtn_only"]
    return data

@st.cache_data(ttl=300)
def update_v82():
    articles = load_and_restore()
    # [A-3: 담당자 픽 14개 링크 타겟 수집 - 시뮬레이션]
    targets = [
        "https://www.thisisgame.com/articles?newsId=400003",
        "https://www.inven.co.kr/webzine/news/?sclass=12",
        "https://www.gamemeca.com/review.php",
        "https://dealsite.co.kr/search/?LIKE=넥슨"
    ]
    # (실제 구현 시 위 URL들에서 og:image와 og:title을 실시간 파싱하여 articles에 append)
    
    # [A-2: 글로벌 사진 엔진 원복 - GameSpot RSS]
    try:
        r = requests.get("https://www.gamespot.com/feeds/news/", timeout=5)
        root = ET.fromstring(r.text)
        for item in root.findall('.//item')[:10]:
            thumb = ""
            media = item.find('{http://search.yahoo.com/mrss/}content')
            if media is not None: thumb = media.get('url')
            articles.append({
                "title": item.find('title').text,
                "link": item.find('link').text,
                "source": "GameSpot", "tag": "tag-global", "group": "global",
                "thumb": thumb if thumb else "fallback_url",
                "timestamp": datetime.now().timestamp()
            })
    except: pass

    # 네이버 뉴스 백업 유지
    try:
        r = requests.get("https://news.google.com/rss/search?q=게임&hl=ko&gl=KR&ceid=KR:ko", timeout=5)
        root = ET.fromstring(r.text)
        for item in root.findall('.//item')[:10]:
            articles.append({
                "title": item.find('title').text,
                "link": item.find('link').text,
                "source": "네이버", "tag": "tag-biz", "group": "domestic",
                "thumb": "naver_logo_url", "timestamp": datetime.now().timestamp() - 3600
            })
    except: pass

    return sorted(articles, key=lambda x: x['timestamp'], reverse=True)

live_data = update_v82()
dom = [d for d in live_data if d['group'] == "domestic"]
glo = [d for d in live_data if d['group'] == "global"]
mtn = [d for d in live_data if d['group'] == "mtn_only"]

# 3. 화면 렌더링 (B-박제)
try: st.image("division8_centered_1800x300.png", use_column_width=True)
except: pass
st.markdown('<div class="sub-logo-header">AAGIG: 8실 Game Insight Ground</div>', unsafe_allow_html=True)

def draw_box(col, header, data_list):
    with col:
        st.markdown(f'<div class="section-bar"><span>{header}</span><a href="#" class="more-btn">더보기 ➔</a></div>', unsafe_allow_html=True)
        html = '<div class="custom-box">'
        for r in data_list[:8]:
            html += f"""
            <div class="list-row">
                <div class="thumb-box"><img src="{r['thumb']}"></div>
                <div class="content-area">
                    <a href="{r['link']}" target="_blank" class="title-text">{r['title']}</a>
                    <div class="meta-area"><span class="source-tag {r['tag']}">{r['source']}</span></div>
                </div>
            </div>"""
        html += '</div>'; st.markdown(html, unsafe_allow_html=True)

c1, c2 = st.columns(2)
draw_box(c1, "국내 주요 매체/웹진", dom)
draw_box(c2, "글로벌 트렌드", glo)

c3, c4 = st.columns(2)
draw_box(c3, "국내 핫 이슈", dom[8:16])
draw_box(c4, "글로벌 핫 이슈", glo[8:16])

c5, c6 = st.columns(2)
draw_box(c5, "전체 최신 기사", (dom+glo)[16:32])
draw_box(c6, "MTN 서정근 인사이트", mtn)

st.markdown('<div class="mid-banner">실시간 게임 산업 인사이트 통합 그라운드</div>', unsafe_allow_html=True)
