import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
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
    .title-text { 
        color: #333 !important; font-weight: 600; font-size: 13px; text-decoration: none !important; 
        display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; 
        overflow: hidden; text-overflow: ellipsis; white-space: normal !important; 
        line-height: 1.4; margin-bottom: 4px; word-break: keep-all;
    }
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

# 3. 번역 엔진 (deep-translator 적용)
def translate_title(text):
    if not re.search('[a-zA-Z]', text) or re.search('[가-힣]', text): return text
    if HAS_TRANSLATOR:
        try:
            translated = GoogleTranslator(source='auto', target='ko').translate(text)
            return "🌏 " + translated
        except:
            pass
    return "🌏 " + text

# 4. 실시간 상대 시간 계산기 (초/분/시간/일 전 계산)
def calculate_relative_time(date_str):
    if not date_str: return "방금 전"
    now = datetime.now()
    
    # 텍스트 내에 이미 상대시간(분 전, 시간 전, ago 등)이 있으면 변환해서 바로 리턴
    if "초 전" in date_str or "분 전" in date_str or "시간 전" in date_str or "일 전" in date_str:
        return date_str.strip()
    if "ago" in date_str.lower():
        num = re.sub(r'[^0-9]', '', date_str) or "1"
        if "sec" in date_str.lower(): return f"{num}초 전"
        if "min" in date_str.lower(): return f"{num}분 전"
        if "hour" in date_str.lower(): return f"{num}시간 전"
        if "day" in date_str.lower(): return f"{num}일 전"
    
    # 날짜 정규식 추출 시도 (예: 2026.03.25 09:22:31 또는 2026-03-25 등)
    numbers = re.findall(r'\d+', date_str)
    if len(numbers) >= 5: # YYYY, MM, DD, HH, MM
        try:
            year, month, day, hour, minute = map(int, numbers[:5])
            if year < 100: year += 2000
            dt = datetime(year, month, day, hour, minute)
            diff = now - dt
            
            # 음수(미래시간) 처리 오류 방지
            if diff.total_seconds() < 0: return "방금 전"
            
            if diff.days > 0: return f"{diff.days}일 전"
            if diff.seconds >= 3600: return f"{diff.seconds // 3600}시간 전"
            if diff.seconds >= 60: return f"{diff.seconds // 60}분 전"
            return f"{diff.seconds}초 전"
        except: pass
    
    return "방금 전" # 파싱 실패 시 기본값

# 5. 데이터 추출 엔진 (7대 매체 총집합)
@st.cache_data(ttl=300)
def fetch_all_data():
    headers = {"User-Agent": "Mozilla/5.0"}
    data = []
    seen = set()

    def add_article(title, link, source, tag, group, thumb, time_str):
        title = title.strip()
        if title in seen or len(title) < 5: return
        
        final_title = translate_title(title) if group == "global" else title
        rel_time = calculate_relative_time(time_str)
        
        # 24시간/1주일 랭킹을 위한 가짜 스코어 (시간 순서대로 점수 부여를 위한 가공)
        score = 1000
        if "분 전" in rel_time: score -= int(re.sub(r'[^0-9]', '', rel_time) or 0)
        elif "시간 전" in rel_time: score -= (int(re.sub(r'[^0-9]', '', rel_time) or 0) * 60)
        elif "일 전" in rel_time: score -= (int(re.sub(r'[^0-9]', '', rel_time) or 0) * 1440)

        data.append({
            "title": final_title, "link": link, "source": source, "tag": tag, 
            "group": group, "thumb": thumb, "time": rel_time, "score": score
        })
        seen.add(title)

    # [1] 네이버 IT/게임
    try:
        r = requests.get("https://news.naver.com/section/105", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for art in soup.select('.sa_item')[:15]:
            t_el = art.select_one('.sa_text_title')
            if t_el:
                link = art.select_one('a')['href']
                time_str = art.select_one('.sa_text_datetime b, .sa_text_datetime').get_text() if art.select_one('.sa_text_datetime') else ""
                add_article(t_el.get_text(), link, "네이버", "tag-biz", "domestic", "", time_str)
    except: pass

    # [2] 지디넷
    try:
        r = requests.get("https://zdnet.co.kr/news/?lstcode=0060", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for art in soup.select('.news_item')[:10]:
            t_el = art.select_one('h2, .subject')
            if t_el:
                link = art.select_one('a')['href']
                time_str = art.select_one('.time').get_text() if art.select_one('.time') else ""
                add_article(t_el.get_text(), "https://zdnet.co.kr"+link if not link.startswith('http') else link, "지디넷", "tag-zd", "domestic", "", time_str)
    except: pass

    # [3] 딜사이트 넥슨 검색
    try:
        r = requests.get("https://dealsite.co.kr/search/?LIKE=%EB%84%A5%EC%8A%A8&SEARCHFIELD=TITLE", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for art in soup.select('.article-list li, .search-result li')[:10]:
            title_el = art.select_one('.title')
            if title_el:
                a_el = title_el.find_parent('a') or title_el.find('a')
                time_el = art.select_one('.pubdate, .date')
                if a_el: add_article(title_el.get_text(), "https://dealsite.co.kr"+a_el['href'], "딜사이트", "tag-ds", "domestic", "", time_el.get_text() if time_el else "")
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

    # [5] 루리웹 게임뉴스
    try:
        r = requests.get("https://bbs.ruliweb.com/news", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for art in soup.select('.list_data, .article_list li')[:10]:
            t_el = art.select_one('.title, .subject')
            if t_el:
                a_el = t_el.find_parent('a') or t_el.find('a')
                time_el = art.select_one('.time')
                if a_el: add_article(t_el.get_text(), a_el['href'], "루리웹", "tag-ruli", "global", "", time_el.get_text() if time_el else "")
    except: pass

    # [6] IGN (해외 영문)
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

    # [7] MTN 서정근 (독립 수집)
    try:
        r = requests.get("https://news.mtn.co.kr/search/%EC%84%9C%EC%A0%95%EA%B7%BC", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for art in soup.select('.news_list li')[:10]:
            title_el = art.select_one('.title')
            if title_el:
                a_el = title_el.find_parent('a') or title_el.find('a')
                time_el = art.select_one('.time, .date')
                if a_el: add_article(title_el.get_text(), "https://news.mtn.co.kr"+a_el['href'] if not a_el['href'].startswith('http') else a_el['href'], "MTN", "tag-mtn", "mtn_only", "", time_el.get_text() if time_el else "")
    except: pass

    return data

live_data = fetch_all_data()

# 6분할 데이터 그룹핑 (점수가 높은 것 = 최신 글 위주로 정렬)
dom = sorted([d for d in live_data if d['group'] == "domestic"], key=lambda x: x['score'], reverse=True)
glo = sorted([d for d in live_data if d['group'] == "global"], key=lambda x: x['score'], reverse=True)
mtn = sorted([d for d in live_data if d['group'] == "mtn_only"], key=lambda x: x['score'], reverse=True)
mixed = sorted([d for d in live_data if d['group'] in ["domestic", "global"]], key=lambda x: x['score'], reverse=True)

# --- 렌더링 ---
try: st.image("division8_centered_1800x300.png", use_column_width=True)
except: pass
st.markdown('<div class="sub-logo-header">AAGIG: 8실 Game Insight Ground</div>', unsafe_allow_html=True)

def draw_box(col, header, data_list):
    with col:
        st.markdown(f'<div class="section-bar"><span>{header}</span><a href="#" style="color:#ccc; font-weight:normal; text-decoration:none; font-size:11px;">더보기 ➔</a></div>', unsafe_allow_html=True)
        html = '<div class="custom-box">'
        for r in data_list[:8]:
            fallback = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44'><rect width='44' height='44' fill='%23eeeeee'/></svg>"
            img_tag = f'<img src="{r["thumb"]}" referrerpolicy="no-referrer" onerror="this.src=\'{fallback}\'">' if r["thumb"] else f'<img src="{fallback}">'
            
            html += f"""
            <div class="list-row">
                <div class="thumb-box">{img_tag}</div>
                <div class="content-area">
                    <a href="{r['link']}" target="_blank" class="title-text">{r['title']}</a>
                    <div class="meta-area">
                        <span class="source-tag {r['tag']}">{r['source']}</span>
                        <span>🕒 {r['time']}</span>
                    </div>
                </div>
            </div>"""
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

# 6분할 레이아웃 적용
r1_c1, r1_c2 = st.columns(2)
draw_box(r1_c1, "국내 주요 매체 (실시간)", dom)
draw_box(r1_c2, "글로벌 & 커뮤니티 트렌드 (실시간)", glo)

r2_c1, r2_c2 = st.columns(2)
draw_box(r2_c1, "국내 24시간 내 최고 이슈", dom[::-1]) # 예시 차이를 위해 역순 
draw_box(r2_c2, "글로벌 24시간 내 최고 이슈", glo[::-1])

r3_c1, r3_c2 = st.columns(2)
draw_box(r3_c1, "1주일 내 최고 이슈", mixed[3:11] if len(mixed) > 3 else mixed)
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

draw_rank(b1, "많이 읽은 뉴스", mixed, "blue")
draw_rank(b2, "실시간 여론 집중", mixed[::-1], "red")
draw_rank(b3, "화제의 키워드", sorted(mixed, key=lambda x: len(x['title'])), "green")

st.markdown('<div class="version-marker">v37.0</div>', unsafe_allow_html=True)
