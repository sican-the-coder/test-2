import streamlit as st
import pandas as pd
import requests
import re
import json
import os
import urllib.parse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET
import difflib
import html
from bs4 import BeautifulSoup

# --- [철칙 1: B 유지] 기존 번역 및 기본 설정 사수 ---
try:
    from deep_translator import GoogleTranslator
    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False

# 1. 페이지 설정
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

# 2. 스타일 시트 (B 영역 디자인 100% 동결)
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

# --- [UI 선출력] 배너와 타이틀을 먼저 그려서 백지화 방지 ---
try: st.image("division8_centered_1800x300.png", use_column_width=True)
except: pass
st.markdown('<div class="sub-logo-header">AAGIG: 8실 Game Insight Ground</div>', unsafe_allow_html=True)

# 3. 보조 로직
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

def get_relative_time(timestamp):
    diff = datetime.now().timestamp() - timestamp
    if diff < 0 or diff > 31536000: return "방금 전"
    if diff < 86400:
        if diff >= 3600: return f"{int(diff // 3600)}시간 전"
        if diff >= 60: return f"{int(diff // 60)}분 전"
        return "방금 전"
    return f"{int(diff // 86400)}일 전"

# 4. DB 및 수집 엔진 (v48: 캐시 초기화)
DB_FILE = "aagig_db_v48.json"
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
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    # --- [1] 안전한 RSS 구역 (글로벌, MTN, 네이버) ---
    rss_feeds = [
        ("https://www.gamespot.com/feeds/news/", "GameSpot", "tag-global", "global", 20),
        ("https://news.google.com/rss/search?q=서정근+MTN&hl=ko&gl=KR&ceid=KR:ko", "MTN", "tag-mtn", "mtn_only", 15),
        ("https://news.google.com/rss/search?q=게임&hl=ko&gl=KR&ceid=KR:ko", "네이버", "tag-biz", "domestic", 3)
    ]
    
    for rss_url, source_name, tag, group, cap in rss_feeds:
        try:
            r = requests.get(rss_url, headers=headers, timeout=5)
            root = ET.fromstring(r.text)
            feed_temp = []
            for item in root.findall('.//item'):
                try:
                    title = item.find('title').text.strip()
                    link = item.find('link').text.strip()
                    if link in existing_links: continue
                    final_title = translate_title(title) if group == "global" else title
                    if is_similar_title(final_title, existing_titles): continue
                    
                    # 썸네일 수집 로직 (GameSpot 등)
                    thumb = ""
                    media = item.find('{http://search.yahoo.com/mrss/}content')
                    if media is not None: thumb = media.get('url')
                    if not thumb:
                        enc = item.find('enclosure')
                        if enc is not None: thumb = enc.get('url')
                    if not thumb:
                        desc = item.find('description')
                        if desc is not None:
                            match = re.search(r'src="([^"]+)"', desc.text)
                            if match: thumb = match.group(1)
                    if not thumb:
                        thumb = f"https://www.google.com/s2/favicons?domain={source_name}.com&sz=128"

                    timestamp = datetime.now().timestamp() # RSS는 시간순서대로 정렬됨
                    feed_temp.append({"title": final_title, "link": link, "source": source_name, "tag": tag, "group": group, "thumb": thumb, "timestamp": timestamp})
                except: pass
            
            for art in feed_temp[:cap]:
                new_articles.append(art)
                existing_links.add(art['link'])
                existing_titles.append(art['title'])
        except: pass

    # --- [2] 14개 정예 링크 직접 스크래핑 구역 (꼼수 폐기) ---
    html_targets = [
        ("https://www.thisisgame.com/articles?newsId=400003&categoryId=0", "TIG", "tag-kr"),
        ("https://www.thisisgame.com/articles?newsId=400004&categoryId=0", "TIG", "tag-kr"),
        ("https://www.thisisgame.com/articles?newsId=400005&categoryId=0", "TIG", "tag-kr"),
        ("https://www.inven.co.kr/webzine/news/?sclass=12&platform=gamereview", "인벤", "tag-inven"),
        ("https://www.inven.co.kr/webzine/news/?sclass=24", "인벤", "tag-inven"),
        ("https://www.gamemeca.com/review.php", "게임메카", "tag-kr"),
        ("https://www.gamemeca.com/feature.php", "게임메카", "tag-kr"),
        ("https://zdnet.co.kr/news/?lstcode=0060", "ZDNet", "tag-kr"),
        ("https://dealsite.co.kr/search/?LIKE=%EB%84%A5%EC%8A%A8&SEARCHFIELD=TITLE_CONTENT", "딜사이트", "tag-biz"),
        ("https://bbs.ruliweb.com/news/board/11?cate=1035,1037,1039", "루리웹", "tag-kr"),
        ("https://www.fetv.co.kr/news/section_list_all.html?sec_no=59", "FETV", "tag-biz")
    ]
    
    # 만화/서적 등 스팸 필터 유지
    blacklist = ['[질문]', '[잡담]', '[단편]', '[연재]', '올림픽', '아시안게임', '만화', '서적']

    for url, source, tag in html_targets:
        try:
            # 3초 룰 적용하여 서버 뻗음 방지
            r = requests.get(url, headers=headers, timeout=3)
            soup = BeautifulSoup(r.text, 'html.parser')
            count = 0
            
            # 범용적이고 안전한 썸네일+기사 추출 휴리스틱
            for a_tag in soup.find_all('a', href=True):
                if count >= 3: break # 각 세부 링크당 3개씩만 가져와서 황금비율 유지
                
                title = a_tag.get_text(strip=True)
                if len(title) < 12 or any(b in title for b in blacklist): continue # 짧은 UI 텍스트 및 스팸 무시
                
                link = a_tag['href']
                if not link.startswith('http'):
                    base = urllib.parse.urlparse(url)
                    link = f"{base.scheme}://{base.netloc}{link}"
                
                if link in existing_links or is_similar_title(title, existing_titles): continue

                # 썸네일 찾기 (a 태그 내부 이미지 우선)
                img_tag = a_tag.find('img')
                if img_tag and img_tag.has_attr('src'):
                    thumb = img_tag['src']
                    if not thumb.startswith('http'):
                        thumb = f"{urllib.parse.urlparse(url).scheme}://{urllib.parse.urlparse(url).netloc}{thumb}"
                else:
                    thumb = f"https://www.google.com/s2/favicons?domain={source}.com&sz=128"

                timestamp = datetime.now().timestamp()
                new_articles.append({"title": title, "link": link, "source": source, "tag": tag, "group": "domestic", "thumb": thumb, "timestamp": timestamp})
                
                existing_links.add(link)
                existing_titles.append(title)
                count += 1
        except: pass

    final_db = sorted((current_db + new_articles), key=lambda x: x['timestamp'], reverse=True)
    save_db(final_db[:300])
    return final_db

# [데이터 수집 시 로딩 스피너 적용]
with st.spinner('14개 정예 웹진에 접속하여 데이터를 직접 수집 중입니다. (최대 10초 소요)'):
    live_data = update_articles()

dom = [d for d in live_data if d['group'] == "domestic"]
glo = [d for d in live_data if d['group'] == "global"]
mtn = [d for d in live_data if d['group'] == "mtn_only"]

# --- 6분할 레이아웃 출력 (html.escape 추가로 양식 깨짐 방벽 전개) ---
def draw_box(col, header, data_list):
    with col:
        st.markdown(f'<div class="section-bar"><span>{header}</span><a href="#" class="more-btn">더보기 ➔</a></div>', unsafe_allow_html=True)
        html_str = '<div class="custom-box">'
        for r in data_list[:8]:
            fallback = f"https://www.google.com/s2/favicons?domain={r['source']}.com&sz=128"
            thumb = r['thumb'] if r['thumb'] else fallback
            region = "KR" if r['group'] != "global" else "GL"
            reg_cls = "tag-kr" if r['group'] != "global" else "tag-gl"
            
            # [핵심] 제목의 <, >, " 특수문자가 HTML을 부수지 못하도록 이스케이프 처리
            safe_title = html.escape(r['title'])
            
            html_str += f"""
            <div class="list-row">
                <div class="thumb-box"><img src="{thumb}" onerror="this.src='{fallback}'"></div>
                <div class="content-area">
                    <a href="{r['link']}" target="_blank" class="title-text">{safe_title}</a>
                    <div class="meta-area">
                        <span class="source-tag {r['tag']}">{r['source']}</span>
                        <span class="source-tag {reg_cls}">{region}</span>
                        <span>🕒 {get_relative_time(r['timestamp'])}</span>
                    </div>
                </div>
            </div>"""
        html_str += '</div>'; st.markdown(html_str, unsafe_allow_html=True)

r1_c1, r1_c2 = st.columns(2)
draw_box(r1_c1, "국내 주요 매체/웹진", dom)
draw_box(r1_c2, "글로벌 트렌드", glo)

r2_c1, r2_c2 = st.columns(2)
draw_box(r2_c1, "국내 핫 이슈", dom[8:16])
draw_box(r2_c2, "글로벌 핫 이슈", glo[8:16])

r3_c1, r3_c2 = st.columns(2)
draw_box(r3_c1, "전체 최신 기사", (dom+glo)[16:32])
draw_box(r3_c2, "MTN 서정근 인사이트", mtn)

st.markdown('<div class="mid-banner">실시간 게임 산업 인사이트 통합 그라운드</div>', unsafe_allow_html=True)
st.markdown('<div class="version-marker">v106.0 (Direct BS4 Scraper & Layout Protector Active)</div>', unsafe_allow_html=True)
