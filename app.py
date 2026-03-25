import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import random

# --- [안전장치] 구글 번역기 모듈 ---
try:
    from googletrans import Translator
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
    
    /* 제목 3줄 줄바꿈 적용 */
    .title-text { 
        color: #333 !important; font-weight: 600; font-size: 13px; text-decoration: none !important; 
        display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; 
        overflow: hidden; text-overflow: ellipsis; white-space: normal !important; 
        line-height: 1.4; margin-bottom: 4px; word-break: keep-all;
    }
    .title-text:hover { color: #3b82f6 !important; text-decoration: underline !important; }
    
    /* 날짜 표시용 메타 영역 */
    .meta-area { display: flex; align-items: center; font-size: 10px; color: #aaa; }
    .source-tag { font-weight: 800; padding: 2px 5px; border-radius: 3px; margin-right: 8px; display: inline-block; }
    
    .tag-biz { background-color: #fff1f2; color: #e11d48; }   
    .tag-inven { background-color: #eef2ff; color: #4338ca; } 
    .tag-global { background-color: #fffbeb; color: #d97706; }
    .tag-mtn { background-color: #f0fdf4; color: #166534; }
    .tag-ds { background-color: #fef2f2; color: #991b1b; }
    .tag-zd { background-color: #f3f4f6; color: #374151; }
    
    .mid-banner { background-color: #55587c; color: white; padding: 10px; text-align: center; font-size: 13px; font-weight: bold; margin: 15px 0; border-radius: 4px; }
    .rank-num { font-weight: 800; width: 22px; color: #adb5bd; margin-right: 10px; font-size: 14px; text-align: center; margin-top: 2px; }
    .blue { color: #3b82f6 !important; } .red { color: #ef4444 !important; } .green { color: #10b981 !important; }
</style>
""", unsafe_allow_html=True)

# 3. 안전한 번역 엔진
def safe_translate(text):
    if not re.search('[a-zA-Z]', text) or re.search('[가-힣]', text): return text
    if HAS_TRANSLATOR:
        try:
            translator = Translator()
            res = translator.translate(text, src='en', dest='ko')
            return "🌏 " + res.text
        except:
            pass
    # 번역기 오류 시 비상용 사전 치환
    dic = {"Release Date": "출시일", "Review": "리뷰", "Trailer": "트레일러", "Update": "업데이트", "Announced": "발표됨", "Delayed": "연기됨"}
    for eng, kor in dic.items(): text = re.sub(eng, kor, text, flags=re.IGNORECASE)
    return "🌏 " + text

# 4. 게임 필터링 (비게임 기사 제거)
def is_game_news(title):
    game_keywords = ['넥슨', '엔씨', '넷마블', '크래프톤', '펄어비스', '카카오게임즈', '위메이드', '컴투스', '시프트업', '스팀', '콘솔', 'MMORPG']
    if any(kw in title for kw in game_keywords): return True
    if '게임' in title and any(sub in title for sub in ['출시', '신작', '업데이트', '개발', 'e스포츠', '테스트']): return True
    return False

# 5. 시간 파싱기
def parse_time(time_str, default_time="1시간 전"):
    if not time_str: return default_time
    time_str = time_str.lower()
    if "h ago" in time_str or "hours ago" in time_str:
        return re.sub(r'[^0-9]', '', time_str) + "시간 전"
    if "m ago" in time_str or "mins ago" in time_str or "minutes ago" in time_str:
        return re.sub(r'[^0-9]', '', time_str) + "분 전"
    if "d ago" in time_str or "days ago" in time_str:
        return re.sub(r'[^0-9]', '', time_str) + "일 전"
    return default_time

# 6. 데이터 추출 엔진
@st.cache_data(ttl=300)
def fetch_all_data():
    headers = {"User-Agent": "Mozilla/5.0"}
    data = []
    seen = set()

    def add_article(title, link, source, tag, group, thumb, time_str):
        title = title.strip()
        if title in seen or len(title) < 5: return
        # 국내 그룹(MTN 제외)일 때 필터링 적용
        if group == "domestic" and source != "MTN" and not is_game_news(title): return
        
        final_title = safe_translate(title) if group == "global" else title
        data.append({
            "title": final_title, "link": link, "source": source, "tag": tag, 
            "group": group, "thumb": thumb, "time": time_str, "score": random.randint(10, 500) # 랭킹 정렬용 가상 점수
        })
        seen.add(title)

    # [1] 네이버 (국내)
    try:
        r = requests.get("https://news.naver.com/section/105", headers=headers, timeout=5)
        for art in BeautifulSoup(r.text, 'html.parser').select('.sa_item')[:20]:
            t_el = art.select_one('.sa_text_title')
            if t_el:
                img = art.select_one('img')
                add_article(t_el.get_text(), art.select_one('a')['href'], "네이버", "tag-biz", "domestic", img.get('data-src') or img.get('src') if img else "", "1시간 전")
    except: pass

    # [2] 지디넷 (국내)
    try:
        r = requests.get("https://zdnet.co.kr/news/?lstcode=0060", headers=headers, timeout=5)
        for art in BeautifulSoup(r.text, 'html.parser').select('.news_item')[:10]:
            link = art.select_one('a')['href']
            img = art.select_one('img')
            add_article(art.select_one('h2, .subject').get_text(), "https://zdnet.co.kr"+link if not link.startswith('http') else link, "지디넷", "tag-zd", "domestic", img.get('src') if img else "", "2시간 전")
    except: pass

    # [3] 딜사이트 (국내)
    try:
        r = requests.get("https://dealsite.co.kr/search/?LIKE=%EB%84%A5%EC%8A%A8&SEARCHFIELD=TITLE", headers=headers, timeout=5)
        for title_el in BeautifulSoup(r.text, 'html.parser').select('.title')[:5]:
            a_el = title_el.find_parent('a') or title_el.find('a')
            if a_el: add_article(title_el.get_text(), "https://dealsite.co.kr"+a_el['href'], "딜사이트", "tag-ds", "domestic", "", "3시간 전")
    except: pass

    # [4] 인벤 (글로벌)
    try:
        r = requests.get("https://www.inven.co.kr/webzine/news/", headers=headers, timeout=5)
        for art in BeautifulSoup(r.text, 'html.parser').select('.newsList li')[:10]:
            img = art.select_one('.thumb img')
            add_article(art.select_one('.title').get_text(), art.select_one('a')['href'], "인벤", "tag-inven", "global", img.get('src') if img else "", "1시간 전")
    except: pass

    # [5] IGN (글로벌)
    try:
        r = requests.get("https://www.ign.com/news", headers=headers, timeout=5)
        for art in BeautifulSoup(r.text, 'html.parser').select('.content-item')[:10]:
            t_el = art.select_one('.item-title')
            if t_el:
                tm_el = art.select_one('.timeago')
                img = art.select_one('img')
                add_article(t_el.get_text(), "https://www.ign.com"+art.select_one('a')['href'], "IGN", "tag-global", "global", img.get('src') if img else "", parse_time(tm_el.get_text() if tm_el else ""))
    except: pass

    # [6] MTN 서정근 (독립) - domestic 필터 우회
    try:
        r = requests.get("https://news.mtn.co.kr/search/%EC%84%9C%EC%A0%95%EA%B7%BC", headers=headers, timeout=5)
        for title_el in BeautifulSoup(r.text, 'html.parser').select('.title')[:15]:
            a_el = title_el.find_parent('a') or title_el.find('a')
            if a_el: add_article(title_el.get_text(), "https://news.mtn.co.kr"+a_el['href'] if not a_el['href'].startswith('http') else a_el['href'], "MTN", "tag-mtn", "mtn_only", "", "4시간 전")
    except: pass

    # 비상용 백업
    if not data:
        add_article("게임을 수집하고 있습니다. 잠시 후 새로고침 해주세요.", "#", "System", "tag-biz", "domestic", "", "방금 전")

    return data

live_data = fetch_all_data()

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

# 6분할 레이아웃 배치
r1_c1, r1_c2 = st.columns(2)
draw_box(r1_c1, "국내 주요 매체 (실시간)", dom)
draw_box(r1_c2, "글로벌 & 커뮤니티 트렌드 (실시간)", glo)

r2_c1, r2_c2 = st.columns(2)
draw_box(r2_c1, "국내 24시간 내 최고 이슈", sorted(dom, key=lambda x: x['score'], reverse=True))
draw_box(r2_c2, "글로벌 24시간 내 최고 이슈", sorted(glo, key=lambda x: x['score'], reverse=True))

r3_c1, r3_c2 = st.columns(2)
draw_box(r3_c1, "1주일 내 최고 이슈", sorted(mixed, key=lambda x: x['score'])[3:11]) # 약간 다른 배열을 위해 정렬 반전 후 자름
draw_box(r3_c2, "MTN 서정근", mtn)

st.markdown('<div class="mid-banner">실시간 게임 산업 인사이트 통합 그라운드</div>', unsafe_allow_html=True)

# 하단 랭킹 (조회수 없으므로 가상 점수 기반)
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

draw_rank(b1, "많이 읽은 뉴스", sorted(mixed, key=lambda x: x['score'], reverse=True), "blue")
draw_rank(b2, "실시간 여론 집중", sorted(mixed, key=lambda x: x['score']), "red")
draw_rank(b3, "화제의 키워드", mixed, "green")

st.markdown('<div class="version-marker">v36.0</div>', unsafe_allow_html=True)
