import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import hashlib

# 1. 페이지 설정
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

# 2. 스타일 시트 (담당자님이 주신 v12.0 코드 100% 그대로 복사)
st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
<style>
    body, .stApp { font-family: "Pretendard Variable", sans-serif !important; background-color: #f2f2f2 !important; }
    @media (min-width: 1200px) { .block-container { max-width: 1100px !important; margin: auto !important; padding-top: 1.5rem !important; } }
    
    .sub-logo-header { text-align: center; color: #3e4156; font-size: 20px; font-weight: 700; margin-top: 5px; margin-bottom: 25px; letter-spacing: -0.04em; }
    
    /* [수정] 더보기 버튼 배치를 위해 섹션바에 flex 추가 */
    .section-bar { background-color: #55587c; color: white; padding: 6px 12px; font-size: 13px; font-weight: 700; border-radius: 4px 4px 0 0; display: flex; justify-content: space-between; align-items: center; }
    .custom-box { background-color: white; border: 1px solid #ddd; border-top: none; margin-bottom: 18px; min-height: 280px; }
    
    .list-row { display: flex; padding: 8px 12px; border-bottom: 1px solid #f2f2f2; align-items: center; text-decoration: none !important; }
    .thumb-box { width: 38px; height: 38px; background-color: #eee; margin-right: 12px; border-radius: 3px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; overflow: hidden; }
    .thumb-box img { width: 100%; height: 100%; object-fit: cover; }
    
    .content-area { flex-grow: 1; overflow: hidden; min-width: 0; text-align: left; }
    
    /* [수정] 제목 스타일: 노멀 텍스트 유지하면서 클릭 가능하게 */
    .title-text { color: #333 !important; font-weight: 600; font-size: 12.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block; text-decoration: none !important; }
    .title-text:hover { color: #3b82f6 !important; text-decoration: underline !important; }

    .source-tag { font-size: 10px; font-weight: 800; padding: 2px 5px; border-radius: 3px; margin-right: 8px; display: inline-block; margin-top: 3px; }
    
    .tag-biz { background-color: #fff1f2; color: #e11d48; }   
    .tag-inven { background-color: #eef2ff; color: #4338ca; } 
    .tag-global { background-color: #fffbeb; color: #d97706; }
    
    .mid-banner { background-color: #55587c; color: white; padding: 10px; text-align: center; font-size: 13px; font-weight: bold; margin: 15px 0; border-radius: 4px; }
    .rank-num { font-weight: 800; width: 22px; color: #adb5bd; margin-right: 10px; font-size: 14px; text-align: center; }
    .blue { color: #3b82f6 !important; } .red { color: #ef4444 !important; } .green { color: #10b981 !important; }
    
    /* 더보기 버튼 스타일 */
    .more-btn { color: #ccc; font-size: 11px; text-decoration: none; font-weight: normal; }
    .more-btn:hover { color: white; }
</style>
""", unsafe_allow_html=True)

# 3. 데이터 엔진 (게임 키워드 필터링 적용)
@st.cache_data(ttl=300)
def fetch_real_live_data():
    headers = {"User-Agent": "Mozilla/5.0"}
    results = []
    seen = set()
    # 게임 관련 키워드
    game_kws = ['게임', '넥슨', '엔씨', '넷마블', '크래프톤', '펄어비스', '카카오게임즈', '출시', '신작', '위메이드', '라인야후', '붉은사막', '배그', '던파']

    try:
        res = requests.get("https://news.naver.com/section/105", headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = soup.select('.sa_item')
        
        for art in articles[:50]:
            title_el = art.select_one('.sa_text_title, .sa_text_strong')
            if title_el:
                title = title_el.get_text(strip=True)
                # [필터링 적용] 게임 관련 키워드가 있을 때만!
                if any(kw in title for kw in game_kws) and title not in seen:
                    press_el = art.select_one('.sa_text_press')
                    img_el = art.select_one('.sa_thumb_inner img, .sa_thumb_link img')
                    thumb = img_el.get('data-src') or img_el.get('src') or "" if img_el else ""
                    source = press_el.get_text(strip=True) if press_el else "뉴스"
                    tag = "tag-biz" if any(x in source for x in ["지디넷", "MTN", "경제", "비즈", "파이낸셜"]) else "tag-inven"
                    
                    results.append({
                        "id": hashlib.md5(title.encode()).hexdigest()[:8],
                        "title": title, "source": source, "tag": tag, "thumb": thumb,
                        "views": 0, "cmts": 0 # 실제 카운팅 데이터는 세션에서 관리
                    })
                    seen.add(title)
    except: pass
    return results

live_data = fetch_real_live_data()

# --- 화면 렌더링 컨트롤 ---
params = st.query_params
post_id = params.get("post_id")
view = params.get("view")

# [상세 페이지]
if post_id:
    if st.button("⬅️ 뒤로가기"): st.query_params.clear(); st.rerun()
    st.info("실시간 기사 미러링 및 본문 크롤링 페이지입니다. (현재 라우팅 테스트 중)")

# [더보기 페이지]
elif view == "all":
    if st.button("⬅️ 대시보드"): st.query_params.clear(); st.rerun()
    st.subheader("전체 게임 이슈 리스트")
    for r in live_data: st.write(f"· [{r['source']}] {r['title']}")

# [메인 페이지] v12.0 디자인
else:
    try: st.image("division8_centered_1800x300.png", use_column_width=True)
    except: pass
    st.markdown('<div class="sub-logo-header">AAGIG: 8실 Game Insight Ground</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    def draw_section(col, header, data_list):
        with col:
            # 섹션 바에 '더보기' 추가
            st.markdown(f'<div class="section-bar"><span>{header}</span><a href="?view=all" target="_self" class="more-btn">더보기 ➔</a></div>', unsafe_allow_html=True)
            html = '<div class="custom-box">'
            for item in data_list[:8]:
                fallback_svg = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='38' height='38'><rect width='38' height='38' fill='%23eeeeee'/></svg>"
                img_url = item["thumb"] if item["thumb"] else fallback_svg
                img_tag = f'<img src="{img_url}" referrerpolicy="no-referrer" onerror="this.src=\'{fallback_svg}\'">'
                
                # [중요] v12.0의 HTML 구조를 글자 하나 안 바꾸고 복원 + 제목에만 링크(<a>) 추가
                html += f'<div class="list-row"><div class="thumb-box">{img_tag}</div><div class="content-area"><a href="?post_id={item["id"]}" target="_self" class="title-text">{item["title"]}</a><span class="source-tag {item["tag"]}">{item["source"]}</span><span style="font-size:10px; color:#aaa;">👁️ 0 | 💬 0</span></div></div>'
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)

    draw_section(c1, "📊 최신 이슈 모음 (네이버 실시간)", live_data)
    draw_section(c2, "🔥 실시간 화제성", live_data[::-1])

st.markdown('<div class="mid-banner">실시간 게임 산업 인사이트 통합 그라운드</div>', unsafe_allow_html=True)
