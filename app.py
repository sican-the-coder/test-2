import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import hashlib

# 1. 페이지 설정 (v12.0 동일)
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

# 2. 스타일 시트 (담당자님이 주신 v12.0 텍스트 100% 복원)
st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
<style>
    body, .stApp { font-family: "Pretendard Variable", sans-serif !important; background-color: #f2f2f2 !important; }
    @media (min-width: 1200px) { .block-container { max-width: 1100px !important; margin: auto !important; padding-top: 1.5rem !important; } }
    
    .sub-logo-header { text-align: center; color: #3e4156; font-size: 20px; font-weight: 700; margin-top: 5px; margin-bottom: 25px; letter-spacing: -0.04em; }
    
    /* v12.0 섹션 바 정차 (더보기 버튼을 위해 레이아웃만 미세 조정) */
    .section-bar { background-color: #55587c; color: white; padding: 6px 12px; font-size: 13px; font-weight: 700; border-radius: 4px 4px 0 0; display: flex; justify-content: space-between; align-items: center; }
    .custom-box { background-color: white; border: 1px solid #ddd; border-top: none; margin-bottom: 18px; min-height: 280px; }
    
    .list-row { display: flex; padding: 8px 12px; border-bottom: 1px solid #f2f2f2; align-items: center; text-decoration: none !important; }
    .thumb-box { width: 38px; height: 38px; background-color: #eee; margin-right: 12px; border-radius: 3px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; overflow: hidden; }
    .thumb-box img { width: 100%; height: 100%; object-fit: cover; }
    
    .content-area { flex-grow: 1; overflow: hidden; min-width: 0; text-align: left; }
    
    /* [핵심] 제목 스타일: v12.0의 title-text 스타일을 그대로 유지하되 <a> 태그 속성 부여 */
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

# 3. 데이터 엔진 (v12.0 수집 로직 + 게임 필터링 추가)
@st.cache_data(ttl=300)
def fetch_real_live_data():
    headers = {"User-Agent": "Mozilla/5.0"}
    results = []
    seen = set()
    game_kws = ['게임', '넥슨', '엔씨', '넷마블', '크래프톤', '펄어비스', '카카오게임즈', '출시', '신작', '라인야후', '위메이드']
    
    try:
        res = requests.get("https://news.naver.com/section/105", headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = soup.select('.sa_item')
        for art in articles:
            title_el = art.select_one('.sa_text_title, .sa_text_strong')
            if title_el:
                title = title_el.get_text(strip=True)
                if any(kw in title for kw in game_kws) and title not in seen:
                    press_el = art.select_one('.sa_text_press')
                    img_el = art.select_one('.sa_thumb_inner img, .sa_thumb_link img')
                    thumb = img_el.get('data-src') or img_el.get('src') or "" if img_el else ""
                    results.append({
                        "id": hashlib.md5(title.encode()).hexdigest()[:8],
                        "title": title, "source": press_el.get_text(strip=True) if press_el else "뉴스",
                        "tag": "tag-biz" if any(x in (press_el.get_text() if press_el else "") for x in ["지디넷", "MTN", "경제"]) else "tag-inven",
                        "thumb": thumb
                    })
                    seen.add(title)
    except: pass
    return results

live_data = fetch_real_live_data()

# --- 화면 렌더링 컨트롤 ---
post_id = st.query_params.get("post_id")
view = st.query_params.get("view")

if post_id: # 상세 페이지
    if st.button("⬅️ 뒤로가기"): st.query_params.clear(); st.rerun()
    st.info("실시간 기사 미러링 페이지입니다.")
elif view == "all": # 더보기 페이지
    if st.button("⬅️ 메인으로"): st.query_params.clear(); st.rerun()
    for r in live_data: st.write(f"· {r['title']}")
else:
    # 4. v12.0과 100% 동일한 상단 배치
    try: st.image("division8_centered_1800x300.png", use_column_width=True)
    except: pass
    st.markdown('<div class="sub-logo-header">AAGIG: 8실 Game Insight Ground</div>', unsafe_allow_html=True)

    # 5. 상단 4분할 격자 (v12.0 함수 구조 복원)
    c1, c2 = st.columns(2)

    def draw_section(col, header, data_list):
        with col:
            # v12.0 디자인에 '더보기' 링크만 우측 끝에 살짝 추가
            st.markdown(f'<div class="section-bar"><span>{header}</span><a href="?view=all" target="_self" style="color:#ccc; font-weight:normal; text-decoration:none; font-size:11px;">더보기 ➔</a></div>', unsafe_allow_html=True)
            html = '<div class="custom-box">'
            for item in data_list[:8]:
                img_url = item["thumb"] if item["thumb"] else "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='38' height='38'><rect width='38' height='38' fill='%23eeeeee'/></svg>"
                # v12.0의 list-row 구조를 100% 동일하게 복원
                html += f'<div class="list-row"><div class="thumb-box"><img src="{img_url}" referrerpolicy="no-referrer"></div><div class="content-area"><a href="?post_id={item["id"]}" target="_self" class="title-text">{item["title"]}</a><span class="source-tag {item["tag"]}">{item["source"]}</span><span style="font-size:10px; color:#aaa;">👁️ 0 | 💬 0</span></div></div>'
            html += '</div>'; st.markdown(html, unsafe_allow_html=True)

    draw_section(c1, "📊 최신 이슈 모음 (네이버 실시간)", live_data)
    draw_section(c2, "🔥 3시간 내 핫이슈 모음", sorted(live_data, key=lambda x: x['title'], reverse=True))
    draw_section(c1, "🕘 9시간 내 핫이슈 모음", live_data[::-1])
    draw_section(c2, "❤️ 24시간 내 하트 가장 많이 받은 이슈", live_data)

    st.markdown('<div class="mid-banner">실시간 게임 산업 인사이트 통합 그라운드</div>', unsafe_allow_html=True)

    # 하단 랭킹 (v12.0 동일)
    b1, b2, b3 = st.columns(3)
    def draw_rank(col, header, data_list, color):
        with col:
            st.markdown(f'<div class="section-bar">{header}</div>', unsafe_allow_html=True)
            html = '<div class="custom-box">'
            for i, item in enumerate(data_list[:15]):
                num = i+1; num_cls = color if num <= 5 else ""
                html += f'<div class="list-row"><span class="rank-num {num_cls}">{num}</span><div class="content-area"><span class="title-text">{item["title"]}</span></div></div>'
            html += '</div>'; st.markdown(html, unsafe_allow_html=True)

    draw_rank(b1, "커뮤니티 인기순", live_data, "blue")
    draw_rank(b2, "많이 읽은 순서", live_data, "red")
    draw_rank(b3, "커뮤니티 댓글순", live_data, "green")
