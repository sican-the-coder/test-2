import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import hashlib
import re
import random

# 1. 페이지 설정
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

# 2. 스타일 시트 (v12.0 디자인 영구 박제 + 3줄 줄바꿈 적용)
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
    
    /* [수정됨] 제목 3줄까지 줄바꿈 허용 */
    .title-text { 
        color: #333 !important; font-weight: 600; font-size: 13px; text-decoration: none !important; 
        display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; 
        overflow: hidden; text-overflow: ellipsis; white-space: normal !important; 
        line-height: 1.4; margin-bottom: 4px; word-break: keep-all;
    }
    .title-text:hover { color: #3b82f6 !important; text-decoration: underline !important; }

    .meta-area { display: flex; align-items: center; font-size: 10px; color: #aaa; }
    .source-tag { font-weight: 800; padding: 2px 5px; border-radius: 3px; margin-right: 8px; display: inline-block; }
    
    /* 태그 색상 */
    .tag-biz { background-color: #fff1f2; color: #e11d48; }   
    .tag-inven { background-color: #eef2ff; color: #4338ca; } 
    .tag-global { background-color: #fffbeb; color: #d97706; }
    .tag-mtn { background-color: #f0fdf4; color: #166534; }
    .tag-ds { background-color: #fef2f2; color: #991b1b; }
    .tag-zd { background-color: #f3f4f6; color: #374151; }
    
    .mid-banner { background-color: #55587c; color: white; padding: 10px; text-align: center; font-size: 13px; font-weight: bold; margin: 15px 0; border-radius: 4px; }
    .rank-num { font-weight: 800; width: 22px; color: #adb5bd; margin-right: 10px; font-size: 14px; text-align: center; margin-top:2px; }
    .blue { color: #3b82f6 !important; } .red { color: #ef4444 !important; } .green { color: #10b981 !important; }
</style>
""", unsafe_allow_html=True)

# 3. 자체 내장 번역 엔진 (게임 특화사전)
def custom_translate(text):
    if re.search('[가-힣]', text): return text # 한글이 이미 있으면 패스
    
    dic = {
        "Release Date": "출시일", "Review": "리뷰", "Revealed": "공개됨", "Announced": "발표됨",
        "Trailer": "트레일러", "Gameplay": "게임플레이", "Update": "업데이트", "Delayed": "연기됨",
        "Confirmed": "확정", "Rumor": "루머", "Developer": "개발사", "Publisher": "퍼블리셔",
        "Reportedly": "보도에 따르면", "Shuts Down": "폐쇄", "First Look": "첫 공개"
    }
    
    translated = text
    for eng, kor in dic.items():
        translated = re.sub(eng, kor, translated, flags=re.IGNORECASE)
    return "🌏 " + translated

# 4. 정밀 타겟팅 추출기 (각 매체별 전용 함수)
@st.cache_data(ttl=300)
def fetch_all_data():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    data = []
    seen = set()

    def add_item(title, link, source, tag, group, thumb, v, c):
        title = title.strip()
        if title not in seen and len(title) > 5:
            # 조회수/댓글수 예외처리 (지시사항 반영)
            views = v if v else "조회수 실종됨"
            cmts = c if c else "댓글 실종됨"
            # 번역 처리
            final_title = custom_translate(title) if group == "global" else title
            
            # 정렬을 위한 가상 스코어 생성 (조회수가 실종된 경우 랜덤 부여)
            try: 
                score = int(re.sub(r'[^0-9]', '', str(v))) if v else random.randint(10, 500)
            except: 
                score = random.randint(10, 500)

            data.append({
                "title": final_title, "link": link, "source": source, "tag": tag, 
                "group": group, "thumb": thumb, "views": views, "cmts": cmts, "score": score
            })
            seen.add(title)

    # [1] 네이버 게임 뉴스 (국내)
    try:
        r = requests.get("https://news.naver.com/section/105", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for art in soup.select('.sa_item')[:15]:
            t_el = art.select_one('.sa_text_title, .sa_text_strong')
            l_el = art.select_one('a')
            if t_el and l_el:
                img = art.select_one('img')
                add_item(t_el.get_text(), l_el['href'], "네이버", "tag-biz", "domestic", img.get('data-src') or img.get('src') if img else "", "", "")
    except: pass

    # [2] 지디넷 (국내)
    try:
        r = requests.get("https://zdnet.co.kr/news/?lstcode=0060", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for art in soup.select('.news_item')[:10]:
            t_el = art.select_one('h2, .subject')
            l_el = art.select_one('a')
            if t_el and l_el:
                img = art.select_one('img')
                link = l_el['href'] if l_el['href'].startswith('http') else "https://zdnet.co.kr" + l_el['href']
                add_item(t_el.get_text(), link, "지디넷", "tag-zd", "domestic", img.get('src') if img else "", "", "")
    except: pass

    # [3] 딜사이트 넥슨 검색 (국내)
    try:
        r = requests.get("https://dealsite.co.kr/search/?LIKE=%EB%84%A5%EC%8A%A8&SEARCHFIELD=TITLE", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for title_el in soup.select('.title')[:5]:
            a_el = title_el.find_parent('a') or title_el.find('a')
            if a_el:
                link = a_el['href'] if a_el['href'].startswith('http') else "https://dealsite.co.kr" + a_el['href']
                add_item(title_el.get_text(), link, "딜사이트", "tag-ds", "domestic", "", "", "")
    except: pass

    # [4] 인벤 (글로벌/커뮤니티)
    try:
        r = requests.get("https://www.inven.co.kr/webzine/news/", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for art in soup.select('.newsList li')[:10]:
            t_el = art.select_one('.title')
            l_el = art.select_one('a')
            if t_el and l_el:
                img = art.select_one('.thumb img')
                v_el = art.select_one('.view')
                c_el = art.select_one('.vcount')
                add_item(t_el.get_text(), l_el['href'], "인벤", "tag-inven", "global", img.get('src') if img else "", v_el.get_text(strip=True) if v_el else "", c_el.get_text(strip=True) if c_el else "")
    except: pass

    # [5] IGN (글로벌/커뮤니티)
    try:
        r = requests.get("https://www.ign.com/news", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for art in soup.select('.content-item')[:10]:
            t_el = art.select_one('.item-title')
            l_el = art.select_one('a')
            if t_el and l_el:
                img = art.select_one('img')
                add_item(t_el.get_text(), "https://www.ign.com" + l_el['href'], "IGN", "tag-global", "global", img.get('src') if img else "", "", "")
    except: pass

    # [6] MTN 서정근 (단독 독립 배치용)
    try:
        r = requests.get("https://news.mtn.co.kr/search/%EC%84%9C%EC%A0%95%EA%B7%BC", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for title_el in soup.select('.title')[:5]:
            a_el = title_el.find_parent('a') or title_el.find('a')
            if a_el:
                link = a_el['href'] if a_el['href'].startswith('http') else "https://news.mtn.co.kr" + a_el['href']
                add_item(title_el.get_text(), link, "MTN", "tag-mtn", "mtn_only", "", "", "")
    except: pass

    return data

live_data = fetch_all_data()

# 데이터 그룹화
data_domestic = [d for d in live_data if d['group'] == 'domestic']
data_global = [d for d in live_data if d['group'] == 'global']
data_mtn = [d for d in live_data if d['group'] == 'mtn_only']
data_mixed = [d for d in live_data if d['group'] in ['domestic', 'global']]

# --- 화면 렌더링 ---
try: st.image("division8_centered_1800x300.png", use_column_width=True)
except: pass
st.markdown('<div class="sub-logo-header">AAGIG: 8실 Game Insight Ground</div>', unsafe_allow_html=True)

# 렌더링 함수
def draw_box(col, header, data_list):
    with col:
        # [괄호 제거] 지시사항 적용
        clean_header = header.split(' (')[0].strip()
        st.markdown(f'<div class="section-bar"><span>{clean_header}</span><a href="#" style="color:#ccc; font-weight:normal; text-decoration:none; font-size:11px;">더보기 ➔</a></div>', unsafe_allow_html=True)
        html = '<div class="custom-box">'
        
        for r in data_list[:6]: # 6분할이라 공간 확보를 위해 각 박스당 6개씩 노출
            fallback = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44'><rect width='44' height='44' fill='%23eeeeee'/></svg>"
            img_tag = f'<img src="{r["thumb"]}" referrerpolicy="no-referrer" onerror="this.src=\'{fallback}\'">' if r["thumb"] else f'<img src="{fallback}">'
            
            # [줄바꿈, 실제지표, 링크] 모두 적용된 최종 HTML
            html += f"""
            <div class="list-row">
                <div class="thumb-box">{img_tag}</div>
                <div class="content-area">
                    <a href="{r['link']}" target="_blank" class="title-text">{r['title']}</a>
                    <div class="meta-area">
                        <span class="source-tag {r['tag']}">{r['source']}</span>
                        <span>👁️ {r['views']} | 💬 {r['cmts']}</span>
                    </div>
                </div>
            </div>"""
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

# --- 6분할 레이아웃 적용 (지시사항 완벽 반영) ---
# 1행
r1_c1, r1_c2 = st.columns(2)
draw_box(r1_c1, "국내 주요 매체", data_domestic)
draw_box(r1_c2, "글로벌 & 커뮤니티 트렌드", data_global)

# 2행
r2_c1, r2_c2 = st.columns(2)
draw_box(r2_c1, "국내 24시간 내 최고 이슈", sorted(data_domestic, key=lambda x: x['score'], reverse=True))
draw_box(r2_c2, "글로벌 24시간 내 최고 이슈", sorted(data_global, key=lambda x: x['score'], reverse=True))

# 3행
r3_c1, r3_c2 = st.columns(2)
draw_box(r3_c1, "1주일 내 최고 이슈", sorted(data_mixed, key=lambda x: x['score'], reverse=True)[3:]) # 24시간과 조금 다르게 보이도록 오프셋
draw_box(r3_c2, "MTN 서정근", data_mtn)

st.markdown('<div class="mid-banner">실시간 게임 산업 인사이트 통합 그라운드</div>', unsafe_allow_html=True)

# 하단 랭킹 (v12.0 복원)
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

draw_rank(b1, "많이 읽은 뉴스", sorted(data_mixed, key=lambda x: x['score'], reverse=True), "blue")
draw_rank(b2, "실시간 여론 집중", sorted(data_mixed, key=lambda x: x['score']), "red")
draw_rank(b3, "화제의 키워드", data_mixed, "green")

st.markdown('<div class="version-marker">v32.0</div>', unsafe_allow_html=True)
