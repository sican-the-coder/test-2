import streamlit as st
import pandas as pd
import requests
import re
import json
import os
import urllib.parse
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET
import difflib

# --- [철칙 1: B 유지] 기존 번역 및 기본 설정 사수 ---
try:
    from deep_translator import GoogleTranslator
    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False

# 1. 페이지 설정
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

# 2. 스타일 시트 (담당자님 컨펌 B 영역 디자인 100% 박제)
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
    .title-text:hover { color: #3b82f6 !important; text-decoration: underline !important; }
    .meta-area { display: flex; align-items: center; font-size: 10px; color: #aaa; }
    .source-tag { font-weight: 800; padding: 2px 5px; border-radius: 3px; margin-right: 8px; display: inline-block; }
    .tag-biz { background-color: #fff1f2; color: #e11d48; }   
    .tag-inven { background-color: #eef2ff; color: #4338ca; } 
    .tag-global { background-color: #fffbeb; color: #d97706; }
    .tag-mtn { background-color: #f0fdf4; color: #166534; }
    .tag-kr { background-color: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; }
    .tag-gl { background-color: #f3e8ff; color: #6b21a8; border: 1px solid #e9d5ff; }
    .mid-banner { background-color: #55587c; color: white; padding: 10px; text-align: center; font-size: 13px; font-weight: bold; margin: 15px 0; border-radius: 4px; }
    .more-btn { color: #ccc !important; font-weight: normal; text-decoration: none; font-size: 11px; }
</style>
""", unsafe_allow_html=True)

# 3. 보조 로직 (중복 제거 B 사수)
def translate_title(text):
    if not re.search('[a-zA-Z]', text) or re.search('[가-힣]', text): return text
    if HAS_TRANSLATOR:
        try: return GoogleTranslator(source='auto', target='ko').translate(text)
        except: pass
    return text

def is_similar_title(new_title, existing_titles, threshold=0.65):
    for ext_title in existing_titles:
        if difflib.SequenceMatcher(None, new_title, ext_title).ratio() > threshold:
            return True
    return False

# --- [철칙 4: 반복 실수 차단] 날짜 물리적 교정 로직 ---
def get_safe_timestamp(pub_date_str):
    try:
        # 1순위: 표준 파싱
        return parsedate_to_datetime(pub_date_str).timestamp()
    except:
        try:
            # 2순위: 루리웹형 비표준 포맷 (2026-03-26 14:00:00) 낚아채기
            match = re.search(r'(\d{4})-(\d{2})-(\d{2})', pub_date_str)
            if match:
                y, m, d = map(int, match.groups())
                return datetime(y, m, d, tzinfo=timezone.utc).timestamp()
        except: pass
    return datetime.now(timezone.utc).timestamp()

def get_relative_time(timestamp):
    diff = datetime.now().timestamp() - timestamp
    if diff < 0: return "방금 전"
    if diff < 86400:
        if diff >= 3600: return f"{int(diff // 3600)}시간 전"
        if diff >= 60: return f"{int(diff // 60)}분 전"
        return "방금 전"
    return f"{int(diff // 86400)}일 전"

# 4. DB 및 수집 엔진 (v39 갱신 및 B-디자인 철저 보호)
DB_FILE = "aagig_db_v39.json"
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
    return []
def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)

@st.cache_data(ttl=300)
def update_articles():
    current_db = load_db()
    existing_links = {item['link'] for item in current_db}
    existing_titles = [item['title'] for item in current_db]
    new_articles = []

    # 수집 경로 최적화 (국내 매체는 구글 캐시 병행)
    feeds = [
        ("https://www.inven.co.kr/rss/news/", "인벤", "tag-inven", "domestic", "direct"),
        ("https://feeds.feedburner.com/ruliweb", "루리웹", "tag-ruli", "domestic", "direct"),
        ("https://news.google.com/rss/search?q=서정근+MTN&hl=ko&gl=KR&ceid=KR:ko", "MTN", "tag-mtn", "mtn_only", "google_cache"),
        ("https://news.google.com/rss/search?q=게임&hl=ko&gl=KR&ceid=KR:ko", "네이버", "tag-biz", "domestic", "google_cache"),
        ("https://www.gamespot.com/feeds/news/", "GameSpot", "tag-global", "global", "direct")
    ]

    for rss_url, source_name, tag, group, mode in feeds:
        try:
            r = requests.get(rss_url, timeout=5)
            root = ET.fromstring(r.text)
            for item in root.findall('.//item')[:10]:
                try:
                    title = item.find('title').text.strip()
                    link = item.find('link').text.strip()
                    if link in existing_links: continue
                    
                    final_title = translate_title(title) if group == "global" else title
                    if is_similar_title(final_title, existing_titles): continue
                    
                    thumb = ""
                    desc_node = item.find('description')
                    desc_text = desc_node.text if desc_node is not None else ""
                    
                    # [A-사진 추출 로직 고도화]
                    if mode == "direct":
                        # 인벤/글로벌: 원본 태그 탐색
                        media = item.find('{http://search.yahoo.com/mrss/}content')
                        if media is not None: thumb = media.get('url')
                        if not thumb:
                            enc = item.find('enclosure')
                            if enc is not None: thumb = enc.get('url')
                        if not thumb and desc_text:
                            match = re.search(r'<img[^>]+src="([^"]+)"', desc_text)
                            if match: thumb = match.group(1)
                    
                    # 실패 시 혹은 구글 모드일 때: 정적 캐시 낚아채기
                    if not thumb or mode == "google_cache":
                        if desc_text:
                            match = re.search(r'src="([^"]+)"', desc_text)
                            if match: thumb = match.group(1)

                    if not thumb:
                        thumb = f"https://www.google.com/s2/favicons?domain={source_name}.com&sz=128"

                    # [루리웹 날짜 버그 박멸] 물리적 파싱 적용
                    pub_node = item.find('pubDate')
                    timestamp = get_safe_timestamp(pub_node.text) if pub_node is not None else datetime.now().timestamp()
                    
                    new_articles.append({
                        "title": final_title, "link": link, "source": source_name, "tag": tag, 
                        "group": group, "thumb": thumb, "timestamp": timestamp
                    })
                    existing_links.add(link)
                    existing_titles.append(final_title)
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

# --- [철칙 3: B 보존] 화면 렌더링 (배너, 더보기, 레이아웃 100% 동일 유지) ---
try: st.image("division8_centered_1800x300.png", use_column_width=True)
except: pass
st.markdown('<div class="sub-logo-header">AAGIG: 8실 Game Insight Ground</div>', unsafe_allow_html=True)

def draw_box(col, header, data_list):
    with col:
        st.markdown(f'<div class="section-bar"><span>{header}</span><a href="#" class="more-btn">더보기 ➔</a></div>', unsafe_allow_html=True)
        html = '<div class="custom-box">'
        for r in data_list[:8]:
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
st.markdown('<div class="version-marker">v77.0 (Date Bug Fixed & Domestic Image Recovery)</div>', unsafe_allow_html=True)
