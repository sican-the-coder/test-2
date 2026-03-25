import streamlit as st
import pandas as pd
import requests
import re
import json
import os
import urllib.parse
from datetime import datetime
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET  # 파이썬 순정 XML 파서 탑재!

# --- [안전장치] deep-translator 모듈 ---
try:
    from deep_translator import GoogleTranslator
    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False

# 1. 페이지 설정
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

# 2. 스타일 시트 (v12.0 디자인 영구 박제)
st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
<style>
    body, .stApp { font-family: "Pretendard Variable", sans-serif !important; background-color: #f2f2f2 !important; }
    @media (min-width: 1200px) { .block-container { max-width: 1100px !important; margin: auto !important; padding-top: 1.5rem !important; } }
    .sub-logo-header { text-align: center; color: #3e4156; font-size: 20px; font-weight: 700; margin-top: 5px; margin-bottom: 25px; letter-spacing: -0.04em; }
    .section-bar { background-color: #55587c; color: white; padding: 6px 12px; font-size: 13px; font-weight: 700; border-radius: 4px 4px 0 0; display: flex; justify-content: space-between; align-items: center; }
    .custom-box { background-color: white; border: 1px solid #ddd; border-top: none; margin-bottom: 18px; min-height: 280px; }
    .list-row { display: flex; padding: 8px 12px; border-bottom: 1px solid #f2f2f2; align-items: flex-start; text-decoration: none !important; }
    .thumb-box { width: 44px; height: 44px; background-color: #eee; margin-right: 12px; border-radius: 4px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; overflow: hidden; margin-top: 2px; }
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
    .tag-ds { background-color: #fef2f2; color: #991b1b; }
    .tag-zd { background-color: #f3f4f6; color: #374151; }
    .tag-ruli { background-color: #e0f2fe; color: #0369a1; }
    .mid-banner { background-color: #55587c; color: white; padding: 10px; text-align: center; font-size: 13px; font-weight: bold; margin: 15px 0; border-radius: 4px; }
    .rank-num { font-weight: 800; width: 22px; color: #adb5bd; margin-right: 10px; font-size: 14px; text-align: center; margin-top: 2px; }
    .blue { color: #3b82f6 !important; } .red { color: #ef4444 !important; } .green { color: #10b981 !important; }
</style>
""", unsafe_allow_html=True)

# 3. 글로벌 번역기
def translate_title(text):
    if not re.search('[a-zA-Z]', text) or re.search('[가-힣]', text): return text
    if HAS_TRANSLATOR:
        try: return "🌏 " + GoogleTranslator(source='auto', target='ko').translate(text)
        except: pass
    return "🌏 " + text

# 4. 상대 시간 계산기
def get_relative_time(timestamp):
    diff = datetime.now().timestamp() - timestamp
    if diff < 0: return "방금 전"
    if diff >= 86400: return f"{int(diff // 86400)}일 전"
    if diff >= 3600: return f"{int(diff // 3600)}시간 전"
    if diff >= 60: return f"{int(diff // 60)}분 전"
    return f"{int(diff)}초 전"

# 5. 로컬 누적 DB (빈칸 찌꺼기 초기화를 위해 v5로 변경)
DB_FILE = "aagig_db_v5.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
    return []

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)

# 6. 클라우드 IP 차단 우회 엔진 (파이썬 순정 XML 파서 적용)
@st.cache_data(ttl=300)
def update_articles():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}
    current_db = load_db()
    existing_links = {item['link'] for item in current_db}
    new_articles = []

    rss_feeds = [
        ("게임", "네이버", "tag-biz", "domestic"),
        ('게임 source:"지디넷코리아"', "지디넷", "tag-zd", "domestic"),
        ('넥슨 source:"딜사이트"', "딜사이트", "tag-ds", "domestic"),
        ('게임 source:"인벤"', "인벤", "tag-inven", "global"),
        ('게임 source:"루리웹"', "루리웹", "tag-ruli", "global"),
        ('"서정근" source:"머니투데이방송"', "MTN", "tag-mtn", "mtn_only"),
        ("game site:ign.com", "IGN", "tag-global", "global")
    ]

    for query, source_name, tag, group in rss_feeds:
        try:
            if group == "global" and source_name == "IGN":
                url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=en-US&gl=US&ceid=US:en"
            else:
                url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=ko&gl=KR&ceid=KR:ko"
            
            r = requests.get(url, headers=headers, timeout=5)
            
            # [핵심 수정] 파이썬 내장 순정 XML 파서 사용 (링크 증발 버그 영구 해결)
            root = ET.fromstring(r.text)
            
            for item in root.findall('.//channel/item')[:15]:
                title_node = item.find('title')
                link_node = item.find('link')
                pub_node = item.find('pubDate')
                
                raw_title = title_node.text.strip() if title_node is not None and title_node.text else ""
                clean_title = re.sub(r'\s*-\s*[^-]+$', '', raw_title).strip()
                
                if len(clean_title) < 5 or clean_title.upper() == "NAVER": continue
                
                # 이제 링크가 정상적으로 수집됩니다!
                link = link_node.text.strip() if link_node is not None and link_node.text else ""
                if not link or link in existing_links: continue
                
                pubdate_str = pub_node.text if pub_node is not None and pub_node.text else ""
                try:
                    dt = parsedate_to_datetime(pubdate_str)
                    timestamp = dt.timestamp()
                except:
                    timestamp = datetime.now().timestamp()
                
                if datetime.now().timestamp() - timestamp > 604800: continue
                
                final_title = translate_title(clean_title) if group == "global" else clean_title
                
                new_articles.append({
                    "title": final_title, "link": link, "source": source_name, "tag": tag, 
                    "group": group, "thumb": "", "timestamp": timestamp
                })
                existing_links.add(link)
        except Exception as e:
            pass 

    combined_db = current_db + new_articles
    seven_days_ago = datetime.now().timestamp() - 604800
    valid_db = [item for item in combined_db if item['timestamp'] > seven_days_ago]
    valid_db = sorted(valid_db, key=lambda x: x['timestamp'], reverse=True)
    
    save_db(valid_db)
    return valid_db

live_data = update_articles()

dom = [d for d in live_data if d['group'] == "domestic"]
glo = [d for d in live_data if d['group'] == "global"]
mtn = [d for d in live_data if d['group'] == "mtn_only"]
mixed = [d for d in live_data if d['group'] in ["domestic", "global"]]

# --- 화면 렌더링 ---
try: st.image("division8_centered_1800x300.png", use_column_width=True)
except: pass
st.markdown('<div class="sub-logo-header">AAGIG: 8실 Game Insight Ground</div>', unsafe_allow_html=True)

def draw_box(col, header, data_list):
    with col:
        clean_header = header.split(' (')[0].strip()
        st.markdown(f'<div class="section-bar"><span>{clean_header}</span><a href="#" style="color:#ccc; font-weight:normal; text-decoration:none; font-size:11px;">더보기 ➔</a></div>', unsafe_allow_html=True)
        html = '<div class="custom-box">'
        if not data_list:
            html += '<div style="padding:20px; text-align:center; color:#999; font-size:12px;">최초 데이터를 수집하고 있습니다. 잠시 후 새로고침 해주세요!</div>'
        for r in data_list[:8]:
            fallback = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44'><rect width='44' height='44' fill='%23eeeeee'/></svg>"
            img_tag = f'<img src="{r.get("thumb", "")}" referrerpolicy="no-referrer" onerror="this.src=\'{fallback}\'">' if r.get("thumb") else f'<img src="{fallback}">'
            
            real_time_str = get_relative_time(r['timestamp'])
            
            html += f"""
            <div class="list-row">
                <div class="thumb-box">{img_tag}</div>
                <div class="content-area">
                    <a href="{r['link']}" target="_blank" class="title-text">{r['title']}</a>
                    <div class="meta-area">
                        <span class="source-tag {r['tag']}">{r['source']}</span>
                        <span>🕒 {real_time_str}</span>
                    </div>
                </div>
            </div>"""
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

# 6분할 레이아웃
r1_c1, r1_c2 = st.columns(2)
draw_box(r1_c1, "국내 주요 매체", dom)
draw_box(r1_c2, "글로벌 & 커뮤니티 트렌드", glo)

r2_c1, r2_c2 = st.columns(2)
draw_box(r2_c1, "국내 24시간 내 최고 이슈", dom[8:16] if len(dom) > 8 else dom)
draw_box(r2_c2, "글로벌 24시간 내 최고 이슈", glo[8:16] if len(glo) > 8 else glo)

r3_c1, r3_c2 = st.columns(2)
draw_box(r3_c1, "1주일 내 최고 이슈", mixed[16:24] if len(mixed) > 16 else mixed)
draw_box(r3_c2, "MTN 서정근", mtn)

st.markdown('<div class="mid-banner">실시간 게임 산업 인사이트 통합 그라운드</div>', unsafe_allow_html=True)

# 하단 랭킹
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

st.markdown('<div class="version-marker">v44.0</div>', unsafe_allow_html=True)
