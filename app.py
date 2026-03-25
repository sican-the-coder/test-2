import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import hashlib

# 1. 페이지 설정
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

# 2. v12.0 디자인 1:1 복원 CSS (여백, 폰트크기, 색상 고정)
st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
<style>
    body, .stApp { font-family: "Pretendard Variable", sans-serif !important; background-color: #f2f2f2 !important; }
    @media (min-width: 1200px) { .block-container { max-width: 1100px !important; margin: auto !important; padding-top: 1rem !important; } }
    
    .sub-logo-header { text-align: center; color: #3e4156; font-size: 20px; font-weight: 700; margin-top: 5px; margin-bottom: 25px; letter-spacing: -0.04em; }
    .section-bar { background-color: #55587c; color: white; padding: 6px 12px; font-size: 13px; font-weight: 700; border-radius: 4px 4px 0 0; display: flex; justify-content: space-between; align-items: center; }
    .custom-box { background-color: white; border: 1px solid #ddd; border-top: none; margin-bottom: 18px; min-height: 280px; }
    
    /* v12.0의 촘촘한 행 간격 복원 */
    .list-row { display: flex; padding: 8px 12px; border-bottom: 1px solid #f2f2f2; align-items: center; }
    .thumb-box { width: 38px; height: 38px; background-color: #eee; margin-right: 12px; border-radius: 3px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; overflow: hidden; }
    .thumb-box img { width: 100%; height: 100%; object-fit: cover; }
    
    .content-area { flex-grow: 1; overflow: hidden; min-width: 0; text-align: left; }
    
    /* 제목 스타일 (v12.0 노멀 텍스트 복원 + 호버 효과만) */
    .title-link { color: #333 !important; font-weight: 600; font-size: 12.5px; text-decoration: none !important; display: block; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.4; }
    .title-link:hover { color: #3b82f6 !important; text-decoration: underline !important; }
    
    /* 출처 및 메타정보 한 줄 정렬 (v12.0 스타일) */
    .meta-line { display: flex; align-items: center; margin-top: 2px; }
    .source-tag { font-size: 10px; font-weight: 800; padding: 1px 4px; border-radius: 2px; margin-right: 8px; display: inline-block; }
    .tag-biz { background-color: #fff1f2; color: #e11d48; }   
    .tag-inven { background-color: #eef2ff; color: #4338ca; } 
    .meta-text { font-size: 10px; color: #aaa; display: flex; align-items: center; }
    
    .mid-banner { background-color: #55587c; color: white; padding: 10px; text-align: center; font-size: 13px; font-weight: bold; margin: 15px 0; border-radius: 4px; }
    .more-btn { color: #ccc; font-size: 11px; text-decoration: none; font-weight: normal; cursor: pointer; }
    .more-btn:hover { color: white; text-decoration: underline; }
</style>
""", unsafe_allow_html=True)

# 3. 데이터 엔진
@st.cache_data(ttl=300)
def fetch_data():
    headers = {"User-Agent": "Mozilla/5.0"}
    res = []
    seen = set()
    game_kws = ['게임', '넥슨', '엔씨', '넷마블', '크래프톤', '펄어비스', '카카오게임즈', '출시', '라인야후', '붉은사막']
    try:
        r = requests.get("https://news.naver.com/section/105", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for art in soup.select('.sa_item'):
            title_el = art.select_one('.sa_text_title, .sa_text_strong')
            if title_el:
                title = title_el.get_text(strip=True)
                if any(k in title for k in game_kws) and title not in seen:
                    img = art.select_one('img')
                    res.append({
                        "id": hashlib.md5(title.encode()).hexdigest()[:8],
                        "title": title, 
                        "source": art.select_one('.sa_text_press').get_text(strip=True) if art.select_one('.sa_text_press') else "뉴스",
                        "thumb": img.get('data-src') or img.get('src') or "" if img else "",
                        "tag": "tag-biz" if "경제" in title or "비즈" in title else "tag-inven"
                    })
                    seen.add(title)
    except: pass
    return res

live_data = fetch_data()

# --- 페이지 라우팅 제어 ---
params = st.query_params
view = params.get("view", "main")

# [A] 상세 보기 페이지 (글 클릭 시)
if "post_id" in params:
    if st.button("⬅️ 뒤로가기"): st.query_params.clear(); st.rerun()
    st.title("상세 기사 미러링 페이지")
    st.info("선택하신 기사의 본문 수집 내용을 보여주는 화면입니다.")

# [B] 더보기 페이지 (전체 리스트)
elif view == "more":
    st.image("division8_centered_1800x300.png", use_column_width=True)
    if st.button("⬅️ 메인 대시보드로"): st.query_params.clear(); st.rerun()
    st.subheader("전체 게임 이슈 리스트")
    for r in live_data:
        st.write(f"· [{r['source']}] {r['title']}")

# [C] 메인 대시보드 (기본)
else:
    try: st.image("division8_centered_1800x300.png", use_column_width=True)
    except: pass
    st.markdown('<div class="sub-logo-header">AAGIG: 8실 Game Insight Ground</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    def draw_box(col, header, data, view_type):
        with col:
            # 더보기 버튼에 실제 링크(?view=more) 연결
            st.markdown(f'<div class="section-bar"><span>{header}</span><a href="?view=more" target="_self" class="more-btn">더보기 ➔</a></div>', unsafe_allow_html=True)
            html = '<div class="custom-box">'
            for r in data[:8]:
                img = f'<img src="{r["thumb"]}" referrerpolicy="no-referrer">' if r["thumb"] else ''
                # v12.0 구조 복원: 제목 줄 + (출처 뱃지 + 조회수/댓글) 메타 줄
                html += f'<div class="list-row"><div class="thumb-box">{img}</div><div class="content-area"><a href="?post_id={r["id"]}" target="_self" class="title-link">{r["title"]}</a><div class="meta-line"><span class="source-tag {r["tag"]}">{r["source"]}</span><span class="meta-text">👁️ 0 | 💬 0</span></div></div></div>'
            html += '</div>'; st.markdown(html, unsafe_allow_html=True)

    draw_box(c1, "📊 최신 게임 이슈", live_data, "recent")
    draw_box(c2, "🔥 실시간 화제성", live_data[::-1], "hot")

st.markdown('<div class="mid-banner">실시간 게임 산업 인사이트 통합 그라운드</div>', unsafe_allow_html=True)
