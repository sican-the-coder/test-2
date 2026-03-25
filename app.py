import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import hashlib

# 1. 페이지 설정
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

# 2. 세션 상태 초기화 (조회수/댓글 카운팅용)
if 'view_counts' not in st.session_state:
    st.session_state.view_counts = {}
if 'comment_data' not in st.session_state:
    st.session_state.comment_data = {}

# 3. 스타일 시트 (v14.0의 예쁜 디자인 완벽 유지)
st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
<style>
    body, .stApp { font-family: "Pretendard Variable", sans-serif !important; background-color: #f2f2f2 !important; }
    @media (min-width: 1200px) { .block-container { max-width: 1100px !important; margin: auto !important; padding-top: 1.5rem !important; } }
    
    .sub-logo-header { text-align: center; color: #3e4156; font-size: 20px; font-weight: 700; margin-top: 5px; margin-bottom: 25px; letter-spacing: -0.04em; }
    .section-bar { background-color: #55587c; color: white; padding: 6px 12px; font-size: 13px; font-weight: 700; border-radius: 4px 4px 0 0; display: flex; justify-content: space-between; align-items: center; }
    .more-link { color: #ccc; font-size: 11px; text-decoration: none; font-weight: normal; }
    .more-link:hover { color: white; text-decoration: underline; }
    
    .custom-box { background-color: white; border: 1px solid #ddd; border-top: none; margin-bottom: 18px; min-height: 280px; }
    
    .list-row { display: flex; padding: 8px 12px; border-bottom: 1px solid #f2f2f2; align-items: center; }
    .list-row:hover { background-color: #f8faff; }
    
    .thumb-box { width: 38px; height: 38px; background-color: #eee; margin-right: 12px; border-radius: 3px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; overflow: hidden; }
    .thumb-box img { width: 100%; height: 100%; object-fit: cover; }
    
    .content-area { flex-grow: 1; overflow: hidden; min-width: 0; text-align: left; }
    
    /* 제목 링크 스타일 */
    .title-link { color: #333; font-weight: 600; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block; text-decoration: none; margin-bottom: 2px; transition: color 0.2s; }
    .title-link:hover { color: #3b82f6; text-decoration: underline; }
    
    .source-tag { font-size: 10px; font-weight: 800; padding: 1px 4px; border-radius: 3px; margin-right: 8px; display: inline-block; }
    .tag-biz { background-color: #fff1f2; color: #e11d48; }   
    .tag-inven { background-color: #eef2ff; color: #4338ca; } 
    
    .detail-container { background: white; padding: 30px; border-radius: 8px; border: 1px solid #ddd; margin-top: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    .version-marker { position: fixed; bottom: 5px; right: 10px; color: #888; font-size: 10px; opacity: 0.5; pointer-events: none; }
</style>
""", unsafe_allow_html=True)

# 4. 필터링 함수 (게임/IT 관련 기사만 색출)
def is_game_related(title):
    game_keywords = ['게임', '넥슨', '엔씨', '넷마블', '크래프톤', '펄어비스', '카카오게임즈', '출시', '업데이트', '신작', '스팀', '콘솔', 'e스포츠', '위메이드', '컴투스', '시프트업', '라인야후']
    return any(kw in title for kw in game_keywords)

# 5. 실시간 크롤러 엔진
@st.cache_data(ttl=300)
def fetch_filtered_data():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}
    results = []
    seen = set()

    try:
        res = requests.get("https://news.naver.com/section/105", headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = soup.select('.sa_item')
        
        for art in articles[:60]: 
            title_el = art.select_one('.sa_text_title, .sa_text_strong')
            if title_el:
                title = title_el.get_text(strip=True)
                if title not in seen and is_game_related(title):
                    press_el = art.select_one('.sa_text_press')
                    img_el = art.select_one('.sa_thumb_inner img, .sa_thumb_link img')
                    
                    thumb = img_el.get('data-src') or img_el.get('src') or "" if img_el else ""
                    source = press_el.get_text(strip=True) if press_el else "뉴스"
                    tag = "tag-biz" if any(x in source for x in ["지디넷", "MTN", "경제", "비즈", "파이낸셜"]) else "tag-inven"
                    
                    post_id = hashlib.md5(title.encode()).hexdigest()[:8]
                    
                    results.append({"id": post_id, "title": title, "source": source, "tag": tag, "thumb": thumb})
                    seen.add(title)
    except: pass

    if len(results) < 5:
        samples = [
            {"title": "넥슨 '던파 모바일' 중국 출시 가시화... 기대감 고조", "source": "지디넷", "tag": "tag-biz", "thumb": ""},
            {"title": "크래프톤, 인도 시장 확대... '배그 모바일' 흥행 이어가나", "source": "MTN", "tag": "tag-biz", "thumb": ""},
            {"title": "시프트업 '스텔라 블레이드', 글로벌 콘솔 시장 정조준", "source": "디스이즈게임", "tag": "tag-inven", "thumb": ""},
            {"title": "펄어비스 '붉은사막', 게임스컴 출품 소식에 유저 화들짝", "source": "인벤", "tag": "tag-inven", "thumb": ""}
        ]
        for s in samples:
            s["id"] = hashlib.md5(s["title"].encode()).hexdigest()[:8]
            results.append(s)

    return results

data_list = fetch_filtered_data()

# --- 라우팅 시스템 ---
params = st.query_params
post_id = params.get("post_id")

# [상세 페이지] 글 클릭 시 여기로 이동
if post_id:
    post = next((item for item in data_list if item["id"] == post_id), None)
    
    if st.button("⬅️ 메인 대시보드로 돌아가기"):
        st.query_params.clear()
        st.rerun()

    if post:
        # 조회수 1 증가
        st.session_state.view_counts[post_id] = st.session_state.view_counts.get(post_id, 0) + 1
        current_views = st.session_state.view_counts[post_id]
        
        st.markdown('<div class="detail-container">', unsafe_allow_html=True)
        st.markdown(f"<h2>{post['title']}</h2>", unsafe_allow_html=True)
        st.caption(f"출처: {post['source']} | 조회수: {current_views}회")
        
        if post['thumb']:
            st.image(post['thumb'], width=400)
            
        st.markdown("---")
        st.subheader("💡 본문 내용 (크롤링 데이터)")
        st.info("실제 뉴스 사이트에서 긁어온 본문이 여기에 배치됩니다.")
        
        st.markdown("---")
        cmt_list = st.session_state.comment_data.get(post_id, [])
        st.subheader(f"💬 의견 남기기 (현재 {len(cmt_list)}개)")
        
        with st.form("comment_form"):
            new_cmt = st.text_input("이 이슈에 대한 인사이트를 적어주세요.")
            if st.form_submit_button("등록하기"):
                if new_cmt:
                    if post_id not in st.session_state.comment_data:
                        st.session_state.comment_data[post_id] = []
                    st.session_state.comment_data[post_id].append(new_cmt)
                    st.rerun()
        
        for cmt in reversed(cmt_list):
            st.success(f"↳ {cmt}")
            
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("해당 기사를 찾을 수 없거나 삭제되었습니다.")

# [메인 페이지] 평상시 보이는 화면
else:
    try: st.image("division8_centered_1800x300.png", use_column_width=True)
    except: pass
    st.markdown('<div class="sub-logo-header">AAGIG: 8실 Game Insight Ground</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    def draw_box(col, header, data):
        with col:
            st.markdown(f'<div class="section-bar"><span>{header}</span><a href="#" class="more-link">더보기 ➔</a></div>', unsafe_allow_html=True)
            html = '<div class="custom-box">'
            for item in data[:8]:
                v_count = st.session_state.view_counts.get(item['id'], 0)
                c_count = len(st.session_state.comment_data.get(item['id'], []))
                
                fallback_svg = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='38' height='38'><rect width='38' height='38' fill='%23eeeeee'/><text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' font-size='10' fill='%23999999'>NoImg</text></svg>"
                img_url = item["thumb"] if item["thumb"] else fallback_svg
                img_tag = f'<img src="{img_url}" referrerpolicy="no-referrer" onerror="this.src=\'{fallback_svg}\'">'
                
                # [해결 핵심] 모든 들여쓰기를 없애고 완전히 한 줄의 문자열로 압축. 절대 깨지지 않음!
                html += f'<div class="list-row"><div class="thumb-box">{img_tag}</div><div class="content-area"><a href="?post_id={item["id"]}" target="_self" class="title-link">{item["title"]}</a><span class="source-tag {item["tag"]}">{item["source"]}</span><span style="font-size:10px; color:#aaa;">👁️ {v_count} | 💬 {c_count}</span></div></div>'
                
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)

    draw_box(c1, "📊 최신 게임 이슈", data_list)
    draw_box(c2, "🔥 실시간 화제성 (조회수 기준)", sorted(data_list, key=lambda x: st.session_state.view_counts.get(x['id'], 0), reverse=True))

st.markdown('<div class="version-marker">v15.0</div>', unsafe_allow_html=True)
