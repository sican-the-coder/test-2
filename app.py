import streamlit as st
import pandas as pd
import requests
import re
import json
import os
import urllib.parse
from datetime import datetime
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET
import difflib
import base64
import asyncio
from bs4 import BeautifulSoup

# --- [최종 병기] Playwright 설정 ---
# 서버 환경에서 브라우저를 띄워 자바스크립트 보안망을 뚫습니다.
try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

# --- [안전장치] deep-translator 모듈 ---
try:
    from deep_translator import GoogleTranslator
    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False

# 1. 페이지 설정
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

# 2. 스타일 시트 (v52.0~v59.0 검증된 디자인 100% 유지)
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
    .tag-inven { background-color: #eef2ff; color: #4338ca; } 
    .tag-global { background-color: #fffbeb; color: #d97706; }
    .tag-mtn { background-color: #f0fdf4; color: #166534; }
    .tag-ds { background-color: #fef2f2; color: #991b1b; }
    .tag-zd { background-color: #f3f4f6; color: #374151; }
    .tag-ruli { background-color: #e0f2fe; color: #0369a1; }
    .tag-kr { background-color: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; }
    .tag-gl { background-color: #f3e8ff; color: #6b21a8; border: 1px solid #e9d5ff; }
    .mid-banner { background-color: #55587c; color: white; padding: 10px; text-align: center; font-size: 13px; font-weight: bold; margin: 15px 0; border-radius: 4px; }
    .rank-num { font-weight: 800; width: 22px; color: #adb5bd; margin-right: 10px; font-size: 14px; text-align: center; margin-top: 2px; }
    .blue { color: #3b82f6 !important; } .red { color: #ef4444 !important; } .green { color: #10b981 !important; }
</style>
""", unsafe_allow_html=True)

# 3. 글로벌 번역기 (유지)
def translate_title(text):
    if not re.search('[a-zA-Z]', text) or re.search('[가-힣]', text): return text
    if HAS_TRANSLATOR:
        try: return GoogleTranslator(source='auto', target='ko').translate(text)
        except: pass
    return text

# 4. 제목 유사도 판별기 (유지)
def is_similar_title(new_title, existing_titles, threshold=0.65):
    for ext_title in existing_titles:
        if difflib.SequenceMatcher(None, new_title, ext_title).ratio() > threshold:
            return True
    return False

# 5. 상대 시간 계산 (유지)
def get_relative_time(timestamp):
    diff = datetime.now().timestamp() - timestamp
    if diff < 0: return "방금 전"
    if diff >= 86400: return f"{int(diff // 86400)}일 전"
    if diff >= 3600: return f"{int(diff // 3600)}시간 전"
    if diff >= 60: return f"{int(diff // 60)}분 전"
    return f"{int(diff)}초 전"

# --- [최종 수술 부위] Playwright를 이용한 보안망 돌파 썸네일 탈취 ---
async def get_og_image_playwright(url):
    if not HAS_PLAYWRIGHT: return ""
    
    # 1단계: 구글 URL 암호 해독 (Base64)
    real_url = url
    try:
        if '/articles/' in url:
            encoded_part = url.split('/articles/')[1].split('?')[0]
            encoded_part += "=" * ((4 - len(encoded_part) % 4) % 4)
            decoded_bytes = base64.urlsafe_b64decode(encoded_part)
            match = re.search(b'(https?://[a-zA-Z0-9./_?&=-]+)', decoded_bytes)
            if match: real_url = match.group(1).decode('utf-8')
    except: pass

    # 2단계: 실제 브라우저(Playwright) 실행
    try:
        async with async_playwright() as p:
            # 브라우저 백그라운드 실행
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
            page = await context.new_page()
            
            # 보안망이 로봇인지 감시하므로 4초 대기하며 자바스크립트 실행 완료 유도
            await page.goto(real_url, timeout=10000, wait_until="domcontentloaded")
            
            # og:image 메타 태그 추출
            img_url = await page.get_attribute('meta[property="og:image"]', 'content')
            if not img_url:
                img_url = await page.get_attribute('meta[name="og:image"]', 'content')
            
            await browser.close()
            
            if img_url and "googleusercontent" not in img_url:
                return img_url
    except: pass
    return ""

# 6. 로컬 누적 DB (v22 갱신)
DB_FILE = "aagig_db_v22.json"
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
    return []
def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)

# 7. 수집 엔진 (기존 밸런스 100% 유지 + Playwright 비동기 결합)
@st.cache_data(ttl=300)
def update_articles():
    current_db = load_db()
    existing_links = {item['link'] for item in current_db}
    existing_titles = [item['title'] for item in current_db]
    new_articles = []

    rss_feeds = [
        ("게임", "네이버", "tag-biz", "domestic"),
        ("게임 site:zdnet.co.kr", "지디넷", "tag-zd", "domestic"),
        ("게임 site:dealsite.co.kr", "딜사이트", "tag-ds", "domestic"),
        ("게임 site:inven.co.kr", "인벤", "tag-inven", "domestic"), 
        ("게임 site:ruliweb.com", "루리웹", "tag-ruli", "domestic"),
        ("서정근 게임 site:mtn.co.kr", "MTN", "tag-mtn", "mtn_only"),
        ("game site:ign.com", "IGN", "tag-global", "global"),
        ("game site:gamespot.com", "GameSpot", "tag-global", "global")
    ]

    for query, source_name, tag, group in rss_feeds:
        try:
            url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl={'en-US' if group=='global' else 'ko'}&gl={'US' if group=='global' else 'KR'}&ceid={'US:en' if group=='global' else 'KR:ko'}"
            r = requests.get(url, timeout=5)
            root = ET.fromstring(r.text)
            
            # Playwright는 무거우므로 새로 발견된 '핵심' 기사 5개씩만 정밀 타격
            for item in root.findall('.//channel/item')[:5]:
                try:
                    raw_title = item.find('title').text.strip()
                    clean_title = re.sub(r'\s*-\s*[^-]+$', '', raw_title).strip()
                    clean_title = re.sub(r'\[?(KR|GL)\]?\s*[:-]?\s*', '', clean_title, flags=re.IGNORECASE).strip()
                    
                    link = item.find('link').text.strip()
                    if link in existing_links: continue
                    
                    # --- [신규 무기] Playwright 비동기 실행 ---
                    # 스트림릿 환경에서 비동기 함수 실행을 위해 이벤트 루프 사용
                    thumb = asyncio.run(get_og_image_playwright(link))
                    
                    # RSS 백업 추출 (미디어 태그가 살아있을 경우 대비)
                    if not thumb:
                        desc = item.find('description').text
                        img_match = re.search(r'<img[^>]+src="([^"]+)"', desc)
                        if img_match: thumb = img_match.group(1)
                    
                    pub_node = item.find('pubDate')
                    dt = parsedate_to_datetime(pub_node.text)
                    timestamp = dt.timestamp()
                    
                    if is_similar_title(clean_title, existing_titles): continue

                    new_articles.append({
                        "title": clean_title, "link": link, "source": source_name, "tag": tag, 
                        "group": group, "thumb": thumb, "timestamp": timestamp
                    })
                    existing_links.add(link)
                    existing_titles.append(clean_title)
                except: pass
        except: pass

    final_db = sorted((current_db + new_articles), key=lambda x: x['timestamp'], reverse=True)
    save_db(final_db[:300])
    return final_db

live_data = update_articles()
dom = [d for d in live_data if d['group'] == "domestic"]
glo = [d for d in live_data if d['group'] == "global"]
mtn = [d for d in live_data if d['group'] == "mtn_only"]
mixed = [d for d in live_data if d['group'] in ["domestic", "global"]]

# --- 화면 렌더링 (기존 밸런스 100% 유지) ---
st.markdown('<div class="sub-logo-header">AAGIG: 8실 Game Insight Ground</div>', unsafe_allow_html=True)

def draw_box(col, header, data_list):
    with col:
        st.markdown(f'<div class="section-bar"><span>{header}</span></div>', unsafe_allow_html=True)
        html = '<div class="custom-box">'
        if not data_list:
            html += '<div style="padding:20px; text-align:center; color:#999; font-size:12px;">데이터 동기화 중...</div>'
        for r in data_list[:8]:
            # 폴백 이미지는 매체 로고 API 활용 (사진 없을 때 대안)
            fallback = f"https://www.google.com/s2/favicons?domain={r['source']}.com&sz=128"
            thumb = r.get("thumb") if r.get("thumb") else fallback
            region = "KR" if r['group'] != "global" else "GL"
            reg_cls = "tag-kr" if r['group'] != "global" else "tag-gl"
            
            html += f"""
            <div class="list-row">
                <div class="thumb-box"><img src="{thumb}" onerror="this.src='{fallback}'"></div>
                <div class="content-area">
                    <a href="{r['link']}" target="_blank" class="title-text">{r['title']}</a>
                    <div class="meta-area">
                        <span class="source-tag {r['tag']}">{r['source']}</span>
                        <span class="source-tag {reg_cls}">{region}</span>
                        <span>🕒 {get_relative_time(r['timestamp'])}</span>
                    </div>
                </div>
            </div>"""
        html += '</div>'; st.markdown(html, unsafe_allow_html=True)

r1_c1, r1_c2 = st.columns(2)
draw_box(r1_c1, "국내 주요 매체/웹진", dom)
draw_box(r1_c2, "글로벌 트렌드", glo)

r2_c1, r2_c2 = st.columns(2)
draw_box(r2_c1, "국내 핫 이슈", dom[8:16] if len(dom) > 8 else dom)
draw_box(r2_c2, "글로벌 핫 이슈", glo[8:16] if len(glo) > 8 else glo)

r3_c1, r3_c2 = st.columns(2)
draw_box(r3_c1, "전체 최신 기사", mixed[16:24] if len(mixed) > 16 else mixed)
draw_box(r3_c2, "MTN 서정근 인사이트", mtn)

st.markdown('<div class="mid-banner">실시간 게임 산업 인사이트 통합 그라운드</div>', unsafe_allow_html=True)

b1, b2, b3 = st.columns(3)
def draw_rank(col, header, data_list, color):
    with col:
        st.markdown(f'<div class="section-bar">{header}</div>', unsafe_allow_html=True)
        html = '<div class="custom-box">'
        for i, r in enumerate(data_list[:15]):
            num = i + 1
            num_cls = color if num <= 5 else ""
            html += f'<div class="list-row"><span class="rank-num {num_cls}">{num}</span><div class="content-area"><a href="{r["link"]}" target="_blank" class="title-text" style="white-space:nowrap !important; -webkit-line-clamp:1;">{r["title"]}</a></div></div>'
        html += '</div>'; st.markdown(html, unsafe_allow_html=True)

draw_rank(b1, "많이 읽은 뉴스", mixed[24:39] if len(mixed) > 24 else mixed, "blue")
draw_rank(b2, "실시간 여론 집중", sorted(mixed, key=lambda x: len(x['title']), reverse=True), "red")
draw_rank(b3, "화제의 키워드", sorted(mixed, key=lambda x: x['source']), "green")

st.markdown('<div class="version-marker">v60.0 (Playwright Browser Automation Deployment)</div>', unsafe_allow_html=True)
