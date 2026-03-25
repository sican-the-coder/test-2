import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

# 1. 페이지 설정
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

# 2. 세션 상태 초기화 (조회수/댓글 카운팅용 데이터베이스 역할)
if 'view_counts' not in st.session_state:
    st.session_state.view_counts = {}
if 'comment_data' not in st.session_state:
    st.session_state.comment_data = {}

# 3. 스타일 시트 (상세 페이지 대응 포함)
st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
<style>
    body, .stApp { font-family: "Pretendard Variable", sans-serif !important; background-color: #f2f2f2 !important; }
    @media (min-width: 1200px) { .block-container { max-width: 1100px !important; margin: auto !important; padding-top: 1rem !important; } }
    
    .sub-logo-header { text-align: center; color: #3e4156; font-size: 20px; font-weight: 700; margin-top: 5px; margin-bottom: 25px; }
    .section-bar { background-color: #55587c; color: white; padding: 6px 12px; font-size: 13px; font-weight: 700; border-radius: 4px 4px 0 0; display: flex; justify-content: space-between; }
    .custom-box { background-color: white; border: 1px solid #ddd; border-top: none; margin-bottom: 18px; min-height: 280px; }
    
    /* 클릭 가능한 리스트 아이템 */
    .list-row { display: flex; padding: 10px 15px; border-bottom: 1px solid #f2f2f2; align-items: center; transition: 0.2s; cursor: pointer; text-decoration: none !important;}
    .list-row:hover { background-color: #f0f4ff; }
    
    .thumb-box { width: 42px; height: 42px; background-color: #eee; margin-right: 15px; border-radius: 4px; flex-shrink: 0; overflow: hidden; }
    .thumb-box img { width: 100%; height: 100%; object-fit: cover; }
    
    .title-text { color: #333; font-weight: 600; font-size: 13px; margin-bottom: 2px; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .source-tag { font-size: 10px; font-weight: 800; padding: 2px 5px; border-radius: 3px; margin-right: 8px; }
    .tag-biz { background-color: #fff1f2; color: #e11d48; }   
    .tag-inven { background-color: #eef2ff; color: #4338ca; } 
    
    /* 상세 페이지 전용 */
    .detail-container { background: white; padding: 30px; border-radius: 8px; border: 1px solid #ddd; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

# 4. [기능 2] 게임 관련 글만 필터링하는 함수
def is_game_related(title):
    game_keywords = ['게임', '넥슨', '엔씨', '넷마블', '크래프톤', '출시', '업데이트', '패치', '모바일', 'PC', '신작', '밸런스', '펄어비스', '스팀', '콘솔']
    return any(kw in title for kw in game_keywords)

# 5. 데이터 수집 함수 (실시간)
@st.cache_data(ttl=600)
def fetch_filtered_data():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}
    results = []
    
    try:
        # 네이버 IT/뉴스 섹션 수집
        res = requests.get("https://news.naver.com/section/105", headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = soup.select('.sa_item')
        
        for art in articles[:40]:
            title_el = art.select_one('.sa_text_title, .sa_text_strong')
            if title_el:
                title = title_el.get_text(strip=True)
                # [기능 2] 게임 키워드가 포함된 경우만 추가
                if is_game_related(title):
                    img_el = art.select_one('img')
                    thumb = img_el.get('data-src') or img_el.get('src') or "" if img_el else ""
                    results.append({
                        "id": str(hash(title)), # 상세 페이지 이동을 위한 고유 ID
                        "title": title,
                        "source": art.select_one('.sa_text_press').get_text(strip=True) if art.select_one('.sa_text_press') else "뉴스",
                        "thumb": thumb,
                        "category": "비즈니스"
                    })
    except: pass
    return results

# --- 라우팅 시스템 (메인 vs 상세 페이지) ---
params = st.query_params
post_id = params.get("post_id")

# 상세 페이지 (글 클릭 시 이동)
if post_id:
    all_data = fetch_filtered_data()
    post = next((item for item in all_data if item["id"] == post_id), None)
    
    if st.button("⬅️ 메인으로 돌아가기"):
        st.query_params.clear()
        st.rerun()

    if post:
        # [기능 4] 조회수 증가
        st.session_state.view_counts[post_id] = st.session_state.view_counts.get(post_id, 0) + 1
        
        st.markdown(f'<div class="detail-container">', unsafe_allow_html=True)
        st.title(post['title'])
        st.caption(f"출처: {post['source']} | 조회수: {st.session_state.view_counts[post_id]}회")
        st.image(post['thumb'] if post['thumb'] else "https://via.placeholder.com/600", width=400)
        
        st.markdown("---")
        st.subheader("💡 본문 내용 (크롤링 모드)")
        st.write("실제 본문 크롤링 데이터가 여기에 표시됩니다. (현재는 데모 모드)")
        
        st.markdown("---")
        st.subheader(f"💬 댓글 ({len(st.session_state.comment_data.get(post_id, []))})")
        # [기능 4] 댓글 달기 기능
        with st.form("comment_form"):
            new_cmt = st.text_input("의견을 남겨주세요")
            if st.form_submit_button("댓글 달기"):
                if post_id not in st.session_state.comment_data: st.session_state.comment_data[post_id] = []
                st.session_state.comment_data[post_id].append(new_cmt)
                st.rerun()
        
        for cmt in st.session_state.comment_data.get(post_id, []):
            st.info(cmt)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.error("해당 글을 찾을 수 없습니다.")

# 메인 페이지
else:
    # 로고 배치
    try: st.image("division8_centered_1800x300.png", use_column_width=True)
    except: pass
    st.markdown('<div class="sub-logo-header">AAGIG: 8실 Game Insight Ground</div>', unsafe_allow_html=True)

    df_list = fetch_filtered_data()
    
    c1, c2 = st.columns(2)
    
    def draw_box(col, header, data):
        with col:
            # [기능 1] 더보기 버튼 추가
            st.markdown(f'<div class="section-bar"><span>{header}</span><span style="cursor:pointer">더보기 ➔</span></div>', unsafe_allow_html=True)
            st.markdown('<div class="custom-box">', unsafe_allow_html=True)
            for r in data[:7]:
                # [기능 3] 클릭 시 상세 페이지로 연결되는 링크 버튼
                v_count = st.session_state.view_counts.get(r['id'], 0)
                c_count = len(st.session_state.comment_data.get(r['id'], []))
                
                # Streamlit의 st.button을 활용해 깔끔한 클릭 구현
                if st.button(f"📄 {r['title'][:25]}...", key=r['id']):
                    st.query_params["post_id"] = r['id']
                    st.rerun()
                
                st.markdown(f"""
                    <div style="padding: 0 15px 10px 15px; font-size: 11px; color: #888; border-bottom: 1px solid #f2f2f2;">
                        <span class="source-tag tag-biz">{r['source']}</span>
                        👁️ {v_count} | 💬 {c_count}
                    </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    draw_box(c1, "📊 최신 게임 이슈", df_list)
    draw_box(c2, "🔥 실시간 화제성", df_list[::-1])

st.markdown('<div class="version-marker">v13.0</div>', unsafe_allow_html=True)
