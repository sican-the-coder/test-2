import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import json
import os
from datetime import datetime, timedelta

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

# 3. 글로벌 기사 번역기 (deep-translator)
def translate_title(text):
    if not re.search('[a-zA-Z]', text) or re.search('[가-힣]', text): return text
    if HAS_TRANSLATOR:
        try: return "🌏 " + GoogleTranslator(source='auto', target='ko').translate(text)
        except: pass
    return "🌏 " + text

# 4. 시간 파싱 및 상대 시간 계산 엔진 (정확도 향상)
def parse_to_timestamp(date_str):
    now = datetime.now()
    if not date_str: return now.timestamp()
    ds = date_str.lower().strip()
    
    # "1시간 전", "3 mins ago" 등 상대시간 문자열 처리
    if "전" in ds or "ago" in ds:
        num = int(re.sub(r'[^0-9]', '', ds) or 1)
        if "초" in ds or "sec" in ds: return (now - timedelta(seconds=num)).timestamp()
        if "분" in ds or "min" in ds: return (now - timedelta(minutes=num)).timestamp()
        if "시간" in ds or "hour" in ds: return (now - timedelta(hours=num)).timestamp()
        if "일" in ds or "day" in ds: return (now - timedelta(days=num)).timestamp()

    # 절대시간 "2026.03.25 09:22" 등 처리
    nums = list(map(int, re.findall(r'\d+', ds)))
    if len(nums) >= 4:
        y, m, d, h = nums[0], nums[1], nums[2], nums[3]
        minute = nums[4] if len(nums) >= 5 else 0
        if y < 100: y += 2000
        if "pm" in ds or "오후" in ds:
            if h < 12: h += 12
        try:
            return datetime(y, m, d, h, minute).timestamp()
        except: pass
    
    return now.timestamp()

def get_relative_time(timestamp):
    diff = datetime.now() - datetime.fromtimestamp(timestamp)
    if diff.total_seconds() < 0: return "방금 전"
    if diff.days > 0: return f"{diff.days}일 전"
    if diff.seconds >= 3600: return f"{diff.seconds // 3600}시간 전"
    if diff.seconds >= 60: return f"{diff.seconds // 60}분 전"
    return f"{int(diff.seconds)}초 전"

# 5. 로컬 누적 DB (JSON 파일) 관리
DB_FILE = "articles_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
    return []

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)

# 6. 전 매체 수집 엔진 (안전 헤더 적용)
@st.cache_data(ttl=300) # 5분마다 갱신
def update_articles():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    current_db = load_db()
    existing_links = {item['link'] for item in current_db}
    new_articles = []

    def add_article(title, link, source, tag, group, thumb, time_str):
        title = title.strip()
        if len(title) < 5 or link in existing_links: return
        
        timestamp = parse_to_timestamp(time_str)
        # 7일(604800초) 지난 기사는 버림
        if datetime.now().timestamp() - timestamp > 604800: return
        
        final_title = translate_title(title) if group == "global" else title
        new_articles.append({
            "title": final_title, "link": link, "source": source, "tag": tag, 
            "group": group, "thumb": thumb, "timestamp": timestamp
        })
        existing_links.add(link)

    # [1] 네이버 '게임' 검색 뉴스 (완벽 필터링)
    try:
        r = requests.get("https://search.naver.com/search.naver?where=news&query=%EA%B2%8C%EC%9E%84", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for art in soup.select('.news_area')[:15]:
            t_el = art.select_one('.news_tit')
            time_el = art.select_one('.info_group span.info')
            if t_el: add_article(t_el.get_text(), t_el['href'], "네이버", "tag-biz", "domestic", "", time_el.get_text() if time_el else "")
    except: pass

    # [2] 지디넷 (게임)
    try:
        r = requests.get("https://zdnet.co.kr/news/?lstcode=0060", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for art in soup.select('.news_item')[:10]:
            t_el = art.select_one('.subject, h2')
            if t_el:
                a_tag = art.select_one('a')
                link = "https://zdnet.co.kr" + a_tag['href'] if not a_tag['href'].startswith('http') else a_tag['href']
                time_el = art.select_one('.time')
                add_article(t_el.get_text(), link, "지디넷", "tag-zd", "domestic", "", time_el.get_text() if time_el else "")
    except: pass

    # [3] 딜사이트 (넥슨)
    try:
        r = requests.get("https://dealsite.co.kr/search/?LIKE=%EB%84%A5%EC%8A%A8&SEARCHFIELD=TITLE", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for art in soup.select('.article-list li')[:10]:
            t_el = art.select_one('.title a, a')
            if t_el:
                link = "https://dealsite.co.kr" + t_el['href'] if not t_el['href'].startswith('http') else t_el['href']
                time_el = art.select_one('.pubdate, .date')
                add_article(t_el.get_text(), link, "딜사이트", "tag-ds", "domestic", "", time_el.get_text() if time_el else "")
    except: pass

    # [4] 인벤
    try:
        r = requests.get("https://www.inven.co.kr/webzine/news/", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for art in soup.select('.newsList li')[:10]:
            t_el = art.select_one('.title')
            if t_el:
                img = art.select_one('.thumb img')
                time_el = art.select_one('.date')
                add_article(t_el.get_text(), art.select_one('a')['href'], "인벤", "tag-inven", "global", img.get('src') if img else "", time_el.get_text() if time_el else "")
    except: pass

    # [5] 루리웹
    try:
        r = requests.get("https://bbs.ruliweb.com/news", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for art in soup.select('.list_data, .article_list li')[:10]:
            t_el = art.select_one('.title, .subject')
            if t_el and t_el.find('a'):
                a_tag = t_el.find('a')
                time_el = art.select_one('.time')
                add_article(a_tag.get_text(), a_tag['href'], "루리웹", "tag-ruli", "global", "", time_el.get_text() if time_el else "")
    except: pass

    # [6] IGN
    try:
        r = requests.get("https://www.ign.com/news", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for art in soup.select('.content-item')[:10]:
            t_el = art.select_one('.item-title')
            if t_el:
                tm_el = art.select_one('.timeago')
                img = art.select_one('img')
                add_article(t_el.get_text(), "https://www.ign.com"+art.select_one('a')['href'], "IGN", "tag-global", "global", img.get('src') if img else "", tm_el.get_text() if tm_el else "")
    except: pass

    # [7] MTN 서정근 (완벽 추출)
    try:
        r = requests.get("https://news.mtn.co.kr/search/%EC%84%9C%EC%A0%95%EA%B7%BC", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for art in soup.select('.news_list li, .search_list li')[:15]:
            t_el = art.select_one('.title')
            if t_el and t_el.find('a'):
                a_tag = t_el.find('a')
                link = "https://news.mtn.co.kr" + a_tag['href'] if not a_tag['href'].startswith('http') else a_tag['href']
                time_el = art.select_one('.date, .time, .info')
                add_article(a_tag.get_text(), link, "MTN", "tag-mtn", "mtn_only", "", time_el.get_text() if time_el else "")
    except: pass

    # 데이터 누적 및 1주일 제한 필터링 후 저장
    combined_db = current_db + new_articles
    seven_days_ago = datetime.now().timestamp() - 604800
    valid_db = [item for item in combined_db if item['timestamp'] > seven_days_ago]
    # 최신 시간순 정렬
    valid_db = sorted(valid_db, key=lambda x: x['timestamp'], reverse=True)
    
    save_db(valid_db)
    return valid_db

live_data = update_articles()

# 그룹핑
dom = [d for d in live_data if d['group'] == "domestic"]
glo = [d for d in live_data if d['group'] == "global"]
mtn = [d for d in live_data if d['group'] == "mtn_only"]
mixed = [d for d in live_data if d['group'] in ["domestic", "global"]]

# --- 렌더링 ---
try: st.image("division8_centered_1800x300.png", use_column_width=True)
except: pass
st.markdown('<div class="sub-logo-header">AAGIG: 8실 Game Insight Ground</div>', unsafe_allow_html=True)

def draw_box(col, header, data_list):
    with col:
        st.markdown(f'<div class="section-bar"><span>{header}</span><a href="#" style="color:#ccc; font-weight:normal; text-decoration:none; font-size:11px;">더보기 ➔</a></div>', unsafe_allow_html=True)
        html = '<div class="custom-box">'
        if not data_list:
            html += '<div style="padding:20px; text-align:center; color:#999; font-size:12px;">데이터가 누적되고 있습니다...</div>'
        for r in data_list[:8]:
            fallback = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44'><rect width='44' height='44' fill='%23eeeeee'/></svg>"
            img_tag = f'<img src="{r["thumb"]}" referrerpolicy="no-referrer" onerror="this.src=\'{fallback}\'">' if r["thumb"] else f'<img src="{fallback}">'
            
            # 여기서 timestamp를 상대시간으로 변환하여 실시간 출력
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
draw_box(r1_c1, "국내 주요 매체 (실시간)", dom)
draw_box(r1_c2, "글로벌 & 커뮤니티 트렌드 (실시간)", glo)

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

st.markdown('<div class="version-marker">v39.0</div>', unsafe_allow_html=True)
