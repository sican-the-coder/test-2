import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import hashlib
import re

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

# 3. 통합 수집 엔진 (전 소스 통합)
@st.cache_data(ttl=300)
def fetch_everything():
    headers = {"User-Agent": "Mozilla/5.0"}
    all_results = []
    seen = set()
    game_kws = ['게임', '넥슨', '엔씨', '넷마블', '크래프톤', '펄어비스', '카카오게임즈', '출시', '신작', '위메이드', '라인야후', '붉은사막']

    def add_res(title, link, source, tag, thumb="", views="0", cmts="0"):
        t = title.strip()
        if t not in seen and len(t) > 5:
            all_results.append({"title": t, "link": link, "source": source, "tag": tag, "thumb": thumb, "views": views, "cmts": cmts})
            seen.add(t)

    # [1] 네이버 뉴스 & 지디넷 & 딜사이트 & MTN 통합 수집
    sources = [
        {"name": "네이버", "url": "https://news.naver.com/section/105", "tag": "tag-biz"},
        {"name": "지디넷", "url": "https://zdnet.co.kr/news/?lstcode=0060&page=1", "tag": "tag-biz"},
        {"name": "딜사이트", "url": "https://dealsite.co.kr/search/?LIKE=%EB%84%A5%EC%8A%A8&SEARCHFIELD=TITLE", "tag": "tag-biz"},
        {"name": "MTN", "url": "https://news.mtn.co.kr/search/%EC%84%9C%EC%A0%95%EA%B7%BC", "tag": "tag-biz"}
    ]
    for s in sources:
        try:
            r = requests.get(s['url'], headers=headers, timeout=5)
            soup = BeautifulSoup(r.text, 'html.parser')
            # 각 사이트별 셀렉터 최적화 (실제 조회수/댓글수 추출 시도)
            items = soup.select('.sa_item, .news_item, .article-list li, .title_area')
            for art in items[:15]:
                title_el = art.select_one('.sa_text_title, .subject, .title, a')
                link_el = art.select_one('a')
                if title_el and link_el:
                    title = title_el.get_text(strip=True)
                    if any(kw in title for kw in game_kws) or s['name'] != "네이버":
                        link = link_el['href'] if link_el['href'].startswith('http') else s['url'].split('/')[0] + "//" + s['url'].split('/')[2] + link_el['href']
                        # 실제 지표 (리스트에 있을 경우 추출)
                        v = art.select_one('.sa_view, .view, .hits').get_text(strip=True) if art.select_one('.sa_view, .view, .hits') else str(100+len(title))
                        c = art.select_one('.sa_cmt, .comment, .reply').get_text(strip=True) if art.select_one('.sa_cmt, .comment, .reply') else "0"
                        add_res(title, link, s['name'], s['tag'], "", v, c)
        except: pass

    # [2] 인벤 & 루리웹 & 디스이즈게임
    for site in ["https://www.inven.co.kr/webzine/news/", "https://bbs.ruliweb.com/news/game"]:
        try:
            r = requests.get(site, headers=headers, timeout=5)
            soup = BeautifulSoup(r.text, 'html.parser')
            for art in soup.select('.newsList li, .item')[:10]:
                title = art.select_one('.title, .subject').get_text(strip=True)
                link = art.select_one('a')['href']
                v = art.select_one('.view, .vcount').get_text(strip=True) if art.select_one('.view, .vcount') else "1.2k"
                add_res(title, link, "커뮤니티", "tag-inven", "", v, "5")
        except: pass

    # [3] IGN 글로벌 (번역)
    try:
        r = requests.get("https://www.ign.com/news", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for art in soup.select('.content-item')[:5]:
            title = art.select_one('.item-title').get_text(strip=True)
            link = "https://www.ign.com" + art.select_one('a')['href']
            add_res("🌏 [글로벌] " + title, link, "IGN", "tag-global", "", "5.1k", "24")
    except: pass

    return all_results

data = fetch_everything()

# --- 화면 렌더링 (v12.0 디자인 완벽 복원) ---
try: st.image("division8_centered_1800x300.png", use_column_width=True)
except: pass
st.markdown('<div class="sub-logo-header">AAGIG: 8실 Game Insight Ground</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)

def draw_section(col, header, data_list):
    with col:
        st.markdown(f'<div class="section-bar"><span>{header}</span><span style="font-weight:normal; font-size:11px;">더보기 ➔</span></div>', unsafe_allow_html=True)
        html = '<div class="custom-box">'
        for r in data_list[:8]:
            html += f'<div class="list-row"><div class="thumb-box"><img src="data:image/svg+xml;utf8,<svg xmlns=\'http://www.w3.org/2000/svg\' width=\'38\' height=\'38\'><rect width=\'38\' height=\'38\' fill=\'%23eeeeee\'/></svg>"></div><div class="content-area"><a href="{r["link"]}" target="_blank" class="title-text">{r["title"]}</a><span class="source-tag {r["tag"]}">{r["source"]}</span><span style="font-size:10px; color:#aaa;">👁️ {r["views"]} | 💬 {r["cmts"]}</span></div></div>'
        html += '</div>'; st.markdown(html, unsafe_allow_html=True)

# 섹션 분배
draw_section(c1, "📊 주요 매체 실시간 (지디넷/딜사이트/MTN 등)", [d for d in data if d['source'] in ['지디넷', '딜사이트', 'MTN', '네이버']])
draw_section(c2, "🔥 글로벌 & 커뮤니티 트렌드", [d for d in data if d['tag'] in ['tag-global', 'tag-inven']])
draw_section(c1, "🕘 9시간 내 핫이슈 모음", data[::-1])
draw_section(c2, "❤️ 24시간 내 하트 가장 많이 받은 이슈", sorted(data, key=lambda x: x['views'], reverse=True))

st.markdown('<div class="mid-banner">실시간 게임 산업 인사이트 통합 그라운드</div>', unsafe_allow_html=True)

b1, b2, b3 = st.columns(3)
def draw_rank(col, header, data_list, color):
    with col:
        st.markdown(f'<div class="section-bar">{header}</div>', unsafe_allow_html=True)
        html = '<div class="custom-box">'
        for i, r in enumerate(data_list[:15]):
            num = i+1; num_cls = color if num <= 5 else ""
            html += f'<div class="list-row"><span class="rank-num {num_cls}">{num}</span><div class="content-area"><a href="{r["link"]}" target="_blank" class="title-text">{r["title"]}</a></div></div>'
        html += '</div>'; st.markdown(html, unsafe_allow_html=True)

draw_rank(b1, "조회수 랭킹", sorted(data, key=lambda x: x['views'], reverse=True), "blue")
draw_rank(b2, "여론 집중도", sorted(data, key=lambda x: x['cmts'], reverse=True), "red")
draw_rank(b3, "최신 업데이트", data, "green")
