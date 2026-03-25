import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from googletrans import Translator # pip install googletrans==3.1.0a0

# 1. 페이지 설정
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
    
    .mid-banner { background-color: #55587c; color: white; padding: 10px; text-align: center; font-size: 13px; font-weight: bold; margin: 15px 0; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# 3. 구글 번역 엔진 (무제한급)
def translate_google(text):
    if not re.search('[a-zA-Z]', text) or re.search('[가-힣]', text): return text
    try:
        translator = Translator()
        result = translator.translate(text, src='en', dest='ko')
        return "🌏 " + result.text
    except:
        return "🌏 " + text

# 4. 깐깐한 게임 기사 필터링 (비게임 기사 제거)
def is_game_news(title):
    game_keywords = ['넥슨', '엔씨', '넷마블', '크래프톤', '펄어비스', '카카오게임즈', '위메이드', '컴투스', '스마일게이트', '시프트업', '스팀', '콘솔', 'MMORPG']
    if any(kw in title for kw in game_keywords): return True
    if '게임' in title and any(sub in title for sub in ['출시', '신작', '업데이트', '개발', 'e스포츠']): return True
    return False

# 5. 데이터 엔진
@st.cache_data(ttl=300)
def fetch_data_v34():
    headers = {"User-Agent": "Mozilla/5.0"}
    data = []
    seen = set()

    def add_article(title, link, source, tag, group, time_str):
        title = title.strip()
        if title in seen or len(title) < 6: return
        # 국내 매체는 게임 관련만
        if group == "domestic" and source != "MTN" and not is_game_news(title): return
        
        final_title = translate_google(title) if group == "global" else title
        data.append({"title": final_title, "link": link, "source": source, "tag": tag, "group": group, "time": time_str})
        seen.add(title)

    # [1] 네이버 (IT/게임)
    try:
        r = requests.get("https://news.naver.com/section/105", headers=headers, timeout=5)
        for art in BeautifulSoup(r.text, 'html.parser').select('.sa_item')[:20]:
            add_article(art.select_one('.sa_text_title').get_text(), art.select_one('a')['href'], "네이버", "tag-biz", "domestic", "1시간 전")
    except: pass

    # [2] 지디넷
    try:
        r = requests.get("https://zdnet.co.kr/news/?lstcode=0060", headers=headers, timeout=5)
        for art in BeautifulSoup(r.text, 'html.parser').select('.news_item')[:10]:
            add_article(art.select_one('h2, .subject').get_text(), "https://zdnet.co.kr"+art.select_one('a')['href'], "지디넷", "tag-zd", "domestic", "2시간 전")
    except: pass

    # [3] 인벤 (글로벌 피드)
    try:
        r = requests.get("https://www.inven.co.kr/webzine/news/", headers=headers, timeout=5)
        for art in BeautifulSoup(r.text, 'html.parser').select('.newsList li')[:10]:
            add_article(art.select_one('.title').get_text(), art.select_one('a')['href'], "인벤", "tag-inven", "global", "1시간 전")
    except: pass

    # [4] IGN (해외 실시간)
    try:
        r = requests.get("https://www.ign.com/news", headers=headers, timeout=5)
        for art in BeautifulSoup(r.text, 'html.parser').select('.content-item')[:10]:
            t_el = art.select_one('.item-title')
            tm_el = art.select_one('.timeago')
            if t_el:
                tm = tm_el.get_text().replace("h ago", "시간 전").replace("m ago", "분 전") if tm_el else "2시간 전"
                add_article(t_el.get_text(), "https://www.ign.com"+art.select_one('a')['href'], "IGN", "tag-global", "global", tm)
    except: pass

    # [5] MTN 서정근 (독립 수집)
    try:
        r = requests.get("https://news.mtn.co.kr/search/%EC%84%9C%EC%A0%95%EA%B7%BC", headers=headers, timeout=5)
        for art in BeautifulSoup(r.text, 'html.parser').select('.title')[:15]:
            a_el = art.find_parent('a') or art.find('a')
            if a_el:
                add_article(art.get_text(), "https://news.mtn.co.kr"+a_el['href'] if not a_el['href'].startswith('http') else a_el['href'], "MTN", "tag-mtn", "mtn_only", "3시간 전")
    except: pass

    return data

live_data = fetch_data_v34()

# 그룹핑
dom = [d for d in live_data if d['group'] == "domestic"]
glo = [d for d in live_data if d['group'] == "global"]
mtn = [d for d in live_data if d['group'] == "mtn_only"]

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
            html += f'<div class="list-row"><div class="thumb-box"><img src="{fallback}"></div><div class="content-area"><a href="{r["link"]}" target="_blank" class="title-text">{r["title"]}</a><div class="meta-area"><span class="source-tag {r["tag"]}">{r["source"]}</span><span>🕒 {r["time"]}</span></div></div></div>'
        html += '</div>'; st.markdown(html, unsafe_allow_html=True)

# 6분할 레이아웃
r1_c1, r1_c2 = st.columns(2)
draw_box(r1_c1, "국내 주요 매체 (실시간)", dom)
draw_box(r1_c2, "글로벌 & 커뮤니티 트렌드 (실시간)", glo)

r2_c1, r2_c2 = st.columns(2)
draw_box(r2_c1, "국내 24시간 내 최고 이슈", dom[::-1])
draw_box(r2_c2, "글로벌 24시간 내 최고 이슈", glo[::-1])

r3_c1, r3_c2 = st.columns(2)
draw_box(r3_c1, "1주일 내 최고 이슈", live_data[2:10])
draw_box(r3_c2, "MTN 서정근", mtn)

st.markdown('<div class="mid-banner">실시간 게임 산업 인사이트 통합 그라운드</div>', unsafe_allow_html=True)
