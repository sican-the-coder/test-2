import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import hashlib

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
    .list-row { display: flex; padding: 8px 12px; border-bottom: 1px solid #f2f2f2; align-items: center; text-decoration: none !important; }
    .thumb-box { width: 38px; height: 38px; background-color: #eee; margin-right: 12px; border-radius: 3px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; overflow: hidden; }
    .thumb-box img { width: 100%; height: 100%; object-fit: cover; }
    .content-area { flex-grow: 1; overflow: hidden; min-width: 0; text-align: left; }
    .title-text { color: #333 !important; font-weight: 600; font-size: 12.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block; text-decoration: none !important; }
    .title-text:hover { color: #3b82f6 !important; text-decoration: underline !important; }
    .source-tag { font-size: 10px; font-weight: 800; padding: 2px 5px; border-radius: 3px; margin-right: 8px; display: inline-block; margin-top: 3px; }
    .tag-biz { background-color: #fff1f2; color: #e11d48; }   
    .tag-inven { background-color: #eef2ff; color: #4338ca; } 
    .tag-global { background-color: #fffbeb; color: #d97706; }
    .mid-banner { background-color: #55587c; color: white; padding: 10px; text-align: center; font-size: 13px; font-weight: bold; margin: 15px 0; border-radius: 4px; }
    .rank-num { font-weight: 800; width: 22px; color: #adb5bd; margin-right: 10px; font-size: 14px; text-align: center; }
    .blue { color: #3b82f6 !important; } .red { color: #ef4444 !important; } .green { color: #10b981 !important; }
</style>
""", unsafe_allow_html=True)

# 3. 데이터 엔진 (통합 수집 + 위트 있는 지표)
@st.cache_data(ttl=300)
def fetch_all_sources():
    headers = {"User-Agent": "Mozilla/5.0"}
    results = []
    seen = set()
    
    # 위트 있는 조회수/댓글 대체 텍스트
    unknown_views = ["비밀리에 보는 중 🤫", "조회수 실종됨 🔎", "나만 아는 띵작 🌟", "조회수 수줍음 😊", "먼지 쌓이는 중 🧹"]
    unknown_cmts = ["침묵 수행 중 🙊", "첫 댓글의 주인공? ✍️", "댓글 가출함 🏃‍♂️", "인사이트 대기 중 💭"]

    def add_data(title, link, source, tag, thumb="", views="", cmts=""):
        t = title.strip()
        if t and t not in seen:
            v = views if views else unknown_views[len(t) % len(unknown_views)]
            c = cmts if cmts else unknown_cmts[len(t) % len(unknown_cmts)]
            results.append({"title": t, "link": link, "source": source, "tag": tag, "thumb": thumb, "views": v, "cmts": c})
            seen.add(t)

    # 1. 네이버 뉴스 (IT/게임)
    try:
        r = requests.get("https://news.naver.com/section/105", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for art in soup.select('.sa_item')[:15]:
            t_el = art.select_one('.sa_text_title, .sa_text_strong')
            l_el = art.select_one('a')
            if t_el and l_el:
                img = art.select_one('img')
                add_data(t_el.get_text(strip=True), l_el['href'], "네이버", "tag-biz", img.get('src', "") if img else "")
    except: pass

    # 2. 지디넷 (게임 섹션)
    try:
        r = requests.get("https://zdnet.co.kr/news/?lstcode=0060&page=1", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            if '/view/?no=' in a['href']:
                title = a.get_text(strip=True)
                if len(title) > 10:
                    add_data(title, "https://zdnet.co.kr" + a['href'], "지디넷", "tag-biz")
    except: pass

    # 3. 인벤 (최신 뉴스)
    try:
        r = requests.get("https://www.inven.co.kr/webzine/news/", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for art in soup.select('.newsList li')[:10]:
            t_el = art.select_one('.title')
            l_el = art.select_one('a')
            if t_el and l_el:
                add_data(t_el.get_text(strip=True), l_el['href'], "인벤", "tag-inven")
    except: pass

    # 4. IGN 글로벌 (번역 접두어)
    try:
        r = requests.get("https://www.ign.com/news", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for art in soup.select('.content-item')[:5]:
            t_el = art.select_one('.item-title')
            l_el = art.select_one('a')
            if t_el and l_el:
                add_data("🌏 [글로벌] " + t_el.get_text(strip=True), "https://www.ign.com" + l_el['href'], "IGN", "tag-global")
    except: pass

    # 비상용 백업 데이터 (모두 실패 시 화면 깨짐 방지)
    if not results:
        add_data("데이터 연결을 다시 시도 중입니다...", "#", "System", "tag-biz")

    return results

all_data = fetch_all_sources()

# [방안 A] 데이터 분배
media_data = [d for d in all_data if d['tag'] == 'tag-biz']
comm_global_data = [d for d in all_data if d['tag'] in ['tag-inven', 'tag-global']]

# --- 화면 렌더링 (v12.0 디자인 박제) ---
try: st.image("division8_centered_1800x300.png", use_column_width=True)
except: pass
st.markdown('<div class="sub-logo-header">AAGIG: 8실 Game Insight Ground</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)

def draw_section(col, header, data_list):
    with col:
        # 더보기 버튼 유지
        st.markdown(f'<div class="section-bar"><span>{header}</span><span style="font-weight:normal; font-size:11px; cursor:pointer;">더보기 ➔</span></div>', unsafe_allow_html=True)
        html = '<div class="custom-box">'
        # 데이터가 부족하면 빈 자리를 보정
        display_list = data_list if data_list else all_data
        for r in display_list[:8]:
            fallback = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='38' height='38'><rect width='38' height='38' fill='%23eeeeee'/></svg>"
            img_tag = f'<img src="{r["thumb"]}" referrerpolicy="no-referrer" onerror="this.src=\'{fallback}\'">' if r["thumb"] else f'<img src="{fallback}">'
            # v12.0 디자인 그대로 한 줄 압축 코딩
            html += f'<div class="list-row"><div class="thumb-box">{img_tag}</div><div class="content-area"><a href="{r["link"]}" target="_blank" class="title-text">{r["title"]}</a><span class="source-tag {r["tag"]}">{r["source"]}</span><span style="font-size:10px; color:#aaa;">👁️ {r["views"]} | 💬 {r["cmts"]}</span></div></div>'
        html += '</div>'; st.markdown(html, unsafe_allow_html=True)

# 섹션 배치 (방안 A)
draw_section(c1, "📊 국내 주요 매체 (네이버/지디넷/딜사이트 등)", media_data)
draw_section(c2, "🔥 커뮤니티 & 글로벌 트렌드 (인벤/IGN 등)", comm_global_data)
draw_section(c1, "🕘 9시간 내 핫이슈 모음", all_data[::-1])
draw_section(c2, "❤️ 24시간 내 가장 뜨거운 소식", sorted(all_data, key=lambda x: len(x['title']), reverse=True))

st.markdown('<div class="mid-banner">실시간 게임 산업 인사이트 통합 그라운드</div>', unsafe_allow_html=True)

# 하단 랭킹 3분할 (v12.0 복원)
b1, b2, b3 = st.columns(3)
def draw_rank(col, header, data_subset, color):
    with col:
        st.markdown(f'<div class="section-bar">{header}</div>', unsafe_allow_html=True)
        html = '<div class="custom-box">'
        for i, r in enumerate(data_subset[:15]):
            num = i + 1
            num_cls = color if num <= 5 else ""
            html += f'<div class="list-row"><span class="rank-num {num_cls}">{num}</span><div class="content-area"><a href="{r["link"]}" target="_blank" class="title-text">{r["title"]}</a></div></div>'
        html += '</div>'; st.markdown(html, unsafe_allow_html=True)

draw_rank(b1, "많이 읽은 뉴스", all_data, "blue")
draw_rank(b2, "실시간 여론 집중", all_data[::-1], "red")
draw_rank(b3, "화제의 키워드", all_data, "green")
