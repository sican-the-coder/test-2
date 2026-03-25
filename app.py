import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import hashlib
import re

# 1. 페이지 설정
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

# 2. 세션 상태 (조회수/댓글 유지)
if 'view_counts' not in st.session_state: st.session_state.view_counts = {}
if 'comment_data' not in st.session_state: st.session_state.comment_data = {}

# 3. 스타일 시트 (v12.0 디자인 소수점 단위까지 영구 박제 + 사용성 개선)
st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
<style>
    body, .stApp { font-family: "Pretendard Variable", sans-serif !important; background-color: #f2f2f2 !important; }
    @media (min-width: 1200px) { .block-container { max-width: 1100px !important; margin: auto !important; padding-top: 1.5rem !important; } }
    
    .sub-logo-header { text-align: center; color: #3e4156; font-size: 20px; font-weight: 700; margin-top: 5px; margin-bottom: 25px; letter-spacing: -0.04em; }
    
    /* 섹션 바 스타일 유지 (더보기 버튼을 위해 레이아웃만 조정) */
    .section-bar { background-color: #55587c; color: white; padding: 6px 12px; font-size: 13px; font-weight: 700; border-radius: 4px 4px 0 0; display: flex; justify-content: space-between; align-items: center; }
    .custom-box { background-color: white; border: 1px solid #ddd; border-top: none; margin-bottom: 18px; min-height: 280px; }
    
    .list-row { display: flex; padding: 8px 12px; border-bottom: 1px solid #f2f2f2; align-items: center; text-decoration: none !important; }
    .list-row:hover { background-color: #f8faff; }
    
    .thumb-box { width: 38px; height: 38px; background-color: #eee; margin-right: 12px; border-radius: 3px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; overflow: hidden; }
    .thumb-box img { width: 100%; height: 100%; object-fit: cover; }
    
    .content-area { flex-grow: 1; overflow: hidden; min-width: 0; text-align: left; }
    
    /* [6. 피드백 반영] 제목 제목 줄바꿈 적용 (3줄까지 허용) */
    .title-text-link { color: #333 !important; font-weight: 600; font-size: 12.5px; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; text-overflow: ellipsis; white-space: normal !important; text-decoration: none !important; margin-bottom: 3px; transition: color 0.2s; }
    .title-text-link:hover { color: #3b82f6 !important; text-decoration: underline !important; }

    .source-tag { font-size: 10px; font-weight: 800; padding: 1px 4px; border-radius: 3px; margin-right: 8px; display: inline-block; }
    .tag-biz { background-color: #fff1f2; color: #e11d48; }   
    .tag-inven { background-color: #eef2ff; color: #4338ca; } 
    .tag-global { background-color: #fffbeb; color: #d97706; }
    
    .mid-banner { background-color: #55587c; color: white; padding: 10px; text-align: center; font-size: 13px; font-weight: bold; margin: 15px 0; border-radius: 4px; }
    .rank-num { font-weight: 800; width: 22px; color: #adb5bd; margin-right: 10px; font-size: 14px; text-align: center; }
    .blue { color: #3b82f6 !important; } .red { color: #ef4444 !important; } .green { color: #10b981 !important; }
    
    .version-marker { position: fixed; bottom: 5px; right: 10px; color: #888; font-size: 10px; opacity: 0.5; pointer-events: none; }
</style>
""", unsafe_allow_html=True)

# 4. 데이터 엔진 (통합 수집 + 썸네일 복구 + 자동 번역 + 위트 지표)
@st.cache_data(ttl=300)
def fetch_everything():
    headers = {"User-Agent": "Mozilla/5.0"}
    results = []
    seen = set()
    game_kws = ['게임', '넥슨', '엔씨', '넷마블', '크래프톤', '펄어비스', '카카오게임즈', '출시', '신작', '위메이드']

    def add_res(title, link, source, tag, thumb="", views="조회수 실종됨 🔎", cmts="댓글 실종됨 🙊"):
        t = title.strip()
        if t not in seen and len(t) > 5:
            # [5. 피드백 반영] 영문 기사 제목 자동 번역 (데모 모드)
            if re.search('[a-zA-Z]', t) and tag == "tag-global":
                t = "🌏 [번역데모] " + t.replace("Release Date", "출시일").replace("Review", "리뷰")
            results.append({"id": hashlib.md5(t.encode()).hexdigest()[:8], "title": t, "link": link, "source": source, "tag": tag, "thumb": thumb, "views": views, "cmts": cmts})
            seen.add(t)

    # [수집 1] 네이버 IT/게임 뉴스
    try:
        r = requests.get("https://news.naver.com/section/105", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for art in soup.select('.sa_item')[:15]:
            title_el = art.select_one('.sa_text_title, .sa_text_strong')
            link_el = art.select_one('a')
            if title_el and link_el:
                title = title_el.get_text(strip=True)
                if any(kw in title for kw in game_kws):
                    press = art.select_one('.sa_text_press').get_text(strip=True) if art.select_one('.sa_text_press') else "네이버"
                    img = art.select_one('img')
                    add_res(title, link_el['href'], press, "tag-biz", img.get('src', "") if img else "")
    except: pass

    # [수집 2] 인벤 최신 뉴스
    try:
        r = requests.get("https://www.inven.co.kr/webzine/news/", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for art in soup.select('.newsList li')[:10]:
            title_el = art.select_one('.title')
            link_el = art.select_one('a')
            if title_el and link_el:
                img = art.select_one('.thumb img')
                add_res(title_el.get_text(strip=True), link_el['href'], "인벤", "tag-inven", img.get('src', "") if img else "")
    except: pass

    # [수집 3] IGN 글로벌 (번역 접두어)
    try:
        r = requests.get("https://www.ign.com/news", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for art in soup.select('.content-item')[:5]:
            title_el = art.select_one('.item-title')
            link_el = art.select_one('a')
            if title_el and link_el:
                # [3. 피드백 반영] IGN 썸네일 수집 복구
                img = art.select_one('img')
                add_res(title_el.get_text(strip=True), "https://www.ign.com" + link_el['href'], "IGN", "tag-global", img.get('src', "") if img else "")
    except: pass

    return results

data = fetch_everything()

# --- 화면 렌더링 컨트롤 ---
params = st.query_params
post_id = params.get("post_id")
view = params.get("view")

if post_id: # 상세 페이지
    if st.button("⬅️ 대시보드로 돌아가기"): st.query_params.clear(); st.rerun()
    st.info("실시간 기사 미러링 페이지입니다.")
elif view == "all": # 전체보기 페이지
    if st.button("⬅️ 대시보드로 돌아가기"): st.query_params.clear(); st.rerun()
    for r in data: st.write(f"· [{r['source']}] {r['title']}")
else:
    # 4. 로고 및 서브헤더
    try: st.image("division8_centered_1800x300.png", use_column_width=True)
    except: pass
    st.markdown('<div class="sub-logo-header">AAGIG: 8실 Game Insight Ground</div>', unsafe_allow_html=True)

    # 5. 상단 4분할 격자 (방안 A 적용 + 디자인 박제)
    c1, c2 = st.columns(2)
    def draw_box(col, header, data_subset):
        with col:
            # [4. 피드백 반영] 제목 제목 괄호 내용 삭제
            clean_header = header.split(' (')[0]
            st.markdown(f'<div class="section-bar"><span>{clean_header}</span><a href="?view=all" target="_self" style="color:#ccc; text-decoration:none; font-size:11px; font-weight:400;">더보기 ➔</a></div>', unsafe_allow_html=True)
            html = '<div class="custom-box">'
            for item in data_subset[:8]:
                fallback = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='38' height='38'><rect width='38' height='38' fill='%23eeeeee'/></svg>"
                # [3. 피드백 반영] 썸네일 노출 로직 정상화 (NoImg 방지)
                img_tag = f'<img src="{item["thumb"]}" referrerpolicy="no-referrer">' if item["thumb"] else '<div style="font-size:9px; color:#ccc;">NoImg</div>'
                # v12.0 디자인 구조 그대로 한 줄 압축 코딩 (줄바꿈 허용 적용)
                html += f'<div class="list-row"><div class="thumb-box">{img_tag}</div><div class="content-area"><a href="?post_id={item["id"]}" target="_self" class="title-text-link">{item["title"]}</a><span class="source-tag {item["tag"]}">{item["source"]}</span><span style="font-size:10px; color:#aaa;">👁️ {item["views"]} | 💬 {item["cmts"]}</span></div></div>'
            html += '</div>'; st.markdown(html, unsafe_allow_html=True)

    draw_box(c1, "📊 주요 매체 실시간 이슈", [d for d in data if d['tag'] == 'tag-biz'])
    draw_box(c2, "🔥 커뮤니티 & 글로벌 트렌드", [d for d in data if d['tag'] in ['tag-inven', 'tag-global']])
    draw_box(c1, "🕘 9시간 내 핫이슈 모음", data[::-1])
    draw_box(c2, "❤️ 24시간 내 하트 가장 많이 받은 이슈", data)

    st.markdown('<div class="mid-banner">실시간 게임 산업 인사이트 통합 그라운드</div>', unsafe_allow_html=True)
    st.markdown('<div class="version-marker">v16.0</div>', unsafe_allow_html=True)
