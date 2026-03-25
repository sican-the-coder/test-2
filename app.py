import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import hashlib

# 1. 페이지 설정
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

# 2. 세션 상태 (조회수/댓글 유지)
if 'view_counts' not in st.session_state: st.session_state.view_counts = {}
if 'comment_data' not in st.session_state: st.session_state.comment_data = {}

# 3. v12.0 디자인 완벽 복원 CSS
st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
<style>
    body, .stApp { font-family: "Pretendard Variable", sans-serif !important; background-color: #f2f2f2 !important; }
    @media (min-width: 1200px) { .block-container { max-width: 1100px !important; margin: auto !important; padding-top: 1rem !important; } }
    .sub-logo-header { text-align: center; color: #3e4156; font-size: 20px; font-weight: 700; margin-top: 5px; margin-bottom: 25px; letter-spacing: -0.04em; }
    .section-bar { background-color: #55587c; color: white; padding: 6px 12px; font-size: 13px; font-weight: 700; border-radius: 4px 4px 0 0; display: flex; justify-content: space-between; align-items: center; }
    .custom-box { background-color: white; border: 1px solid #ddd; border-top: none; margin-bottom: 18px; min-height: 280px; }
    .list-row { display: flex; padding: 8px 12px; border-bottom: 1px solid #f2f2f2; align-items: center; }
    .thumb-box { width: 38px; height: 38px; background-color: #eee; margin-right: 12px; border-radius: 3px; flex-shrink: 0; overflow: hidden; display: flex; align-items: center; justify-content: center; }
    .thumb-box img { width: 100%; height: 100%; object-fit: cover; }
    .content-area { flex-grow: 1; overflow: hidden; min-width: 0; text-align: left; }
    
    /* [피드백 반영] 제목 스타일: 노멀한 텍스트처럼 보이게 고정 */
    .title-link { 
        color: #333 !important; font-weight: 600; font-size: 12.5px; 
        text-decoration: none !important; display: block; 
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; 
    }
    .title-link:hover { color: #3b82f6 !important; text-decoration: underline !important; }
    
    .source-tag { font-size: 10px; font-weight: 800; padding: 2px 5px; border-radius: 3px; margin-right: 8px; display: inline-block; margin-top: 3px; }
    .tag-biz { background-color: #fff1f2; color: #e11d48; }   
    .tag-inven { background-color: #eef2ff; color: #4338ca; } 
    .mid-banner { background-color: #55587c; color: white; padding: 10px; text-align: center; font-size: 13px; font-weight: bold; margin: 15px 0; border-radius: 4px; }
    .rank-num { font-weight: 800; width: 22px; color: #adb5bd; margin-right: 10px; font-size: 14px; text-align: center; }
    .blue { color: #3b82f6 !important; } .red { color: #ef4444 !important; } .green { color: #10b981 !important; }
    .version-marker { position: fixed; bottom: 5px; right: 10px; color: #888; font-size: 10px; opacity: 0.5; }
</style>
""", unsafe_allow_html=True)

# 4. 데이터 엔진 (게임 필터링 포함)
@st.cache_data(ttl=300)
def fetch_game_data():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}
    data = []
    seen = set()
    game_kws = ['게임', '넥슨', '엔씨', '넷마블', '크래프톤', '펄어비스', '카카오게임즈', '출시', '신작', '라인야후', '위메이드']
    try:
        res = requests.get("https://news.naver.com/section/105", headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        for art in soup.select('.sa_item'):
            title = art.select_one('.sa_text_title, .sa_text_strong').get_text(strip=True)
            if any(kw in title for kw in game_kws) and title not in seen:
                img = art.select_one('img')
                data.append({
                    "id": hashlib.md5(title.encode()).hexdigest()[:8],
                    "title": title, "source": art.select_one('.sa_text_press').get_text(strip=True),
                    "thumb": img.get('data-src') or img.get('src') or "" if img else "",
                    "tag": "tag-biz" if "경제" in title or "뉴스" in title else "tag-inven"
                })
                seen.add(title)
    except: pass
    return data

live_data = fetch_game_data()

# --- 라우팅 컨트롤 ---
params = st.query_params
post_id = params.get("post_id")

if post_id: # 상세 페이지
    post = next((item for item in live_data if item["id"] == post_id), None)
    if st.button("⬅️ 메인으로"): st.query_params.clear(); st.rerun()
    if post:
        st.session_state.view_counts[post_id] = st.session_state.view_counts.get(post_id, 0) + 1
        st.title(post['title'])
        st.write(f"조회수: {st.session_state.view_counts[post_id]}")
        st.info("본문 크롤링 준비 중...")
else: # 메인 페이지
    try: st.image("division8_centered_1800x300.png", use_column_width=True)
    except: pass
    st.markdown('<div class="sub-logo-header">AAGIG: 8실 Game Insight Ground</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    def draw_box(col, header, data):
        with col:
            st.markdown(f'<div class="section-bar"><span>{header}</span><span style="font-size:11px; font-weight:normal;">더보기 ➔</span></div>', unsafe_allow_html=True)
            html = '<div class="custom-box">'
            for r in data[:8]:
                v = st.session_state.view_counts.get(r['id'], 0); c = len(st.session_state.comment_data.get(r['id'], []))
                img = f'<img src="{r["thumb"]}" referrerpolicy="no-referrer">' if r["thumb"] else '<div style="font-size:9px; color:#ccc;">NoImg</div>'
                # 깨짐 방지를 위해 들여쓰기 제거 및 한 줄로 압축
                html += f'<div class="list-row"><div class="thumb-box">{img}</div><div class="content-area"><a href="?post_id={r["id"]}" target="_self" class="title-link">{r["title"]}</a><span class="source-tag {r["tag"]}">{r["source"]}</span><span style="font-size:10px; color:#aaa;">👁️ {v} | 💬 {c}</span></div></div>'
            html += '</div>'; st.markdown(html, unsafe_allow_html=True)

    draw_box(c1, "📊 최신 게임 이슈", live_data)
    draw_box(c2, "🔥 실시간 화제성", live_data[::-1])

st.markdown('<div class="mid-banner">실시간 게임 산업 인사이트 통합 그라운드</div>', unsafe_allow_html=True)
st.markdown('<div class="version-marker">v16.0</div>', unsafe_allow_html=True)
