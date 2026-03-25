import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

# 1. 페이지 설정
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

# 2. 스타일 설정 (프리텐다드 + 중앙 정렬)
st.markdown("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
    <style>
    body, .stApp { font-family: "Pretendard Variable", sans-serif !important; background-color: #f2f2f2; }
    @media (min-width: 1200px) { .block-container { max-width: 1200px !important; margin: auto; } }
    .section-bar { background-color: #55587c; color: white; padding: 6px 12px; font-size: 13px; font-weight: 700; border-radius: 3px 3px 0 0; display: flex; justify-content: space-between; }
    .list-container { background-color: white; border: 1px solid #ddd; margin-bottom: 18px; border-top: none; }
    .list-item { display: flex; padding: 8px 12px; border-bottom: 1px solid #f0f0f0; font-size: 12.5px; align-items: center; }
    .tag-source { color: #4338ca; font-weight: 700; margin-right: 10px; min-width: 45px; font-size: 11px; }
    .title-text { color: #333; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex-grow: 1; }
    .main-logo-bar { background-color: #3e4156; padding: 12px 20px; color: white; border-radius: 5px; margin-bottom: 20px; font-weight: 800; font-size: 20px; }
    </style>
""", unsafe_allow_html=True)

# 3. [진짜 크롤링 엔진] 실시간 수집 함수
def fetch_real_data():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    results = []

    # [수집 1] 네이버 뉴스 - 경제/IT (지디넷, MTN 등 기사 수집용)
    try:
        res = requests.get("https://news.naver.com/main/list.naver?mode=LS2D&mid=shm&sid1=105&sid2=229", headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        news_list = soup.select('.list_body li')
        for item in news_list[:10]:
            title = item.select_one('dt:not(.photo) a').get_text(strip=True)
            source = item.select_one('.writing').get_text(strip=True)
            results.append({"title": title, "source": source, "category": "비즈니스", "score": 100})
    except: pass

    # [수집 2] 인벤 - 최신 뉴스
    try:
        res = requests.get("https://www.inven.co.kr/webzine/news/", headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        inven_list = soup.select('.newsList .info')
        for item in inven_list[:10]:
            title = item.select_one('.title').get_text(strip=True)
            results.append({"title": title, "source": "인벤", "category": "커뮤니티", "score": 80})
    except: pass

    # 만약 수집이 안 될 경우를 대비한 가안 (백업용)
    if not results:
        results = [{"title": "데이터를 연결 중입니다...", "source": "AAGIG", "category": "알림", "score": 0}]

    return pd.DataFrame(results)

# 캐시 없이 바로 실행 (테스트용)
df = fetch_real_data()

# --- 화면 렌더링 ---
st.markdown('<div class="main-logo-bar">AAGIG: Game Insight Ground</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)

def draw_real_box(header, data):
    st.markdown(f'<div class="section-bar"><span>{header}</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="list-container">', unsafe_allow_html=True)
    for _, r in data.head(8).iterrows():
        st.markdown(f"""
            <div class="list-item">
                <span class="tag-source">{r['source']}</span>
                <span class="title-text">{r['title']}</span>
            </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c1:
    draw_real_box("📉 비즈니스/IT 실시간 (네이버 통합)", df[df['category'] == '비즈니스'])
with c2:
    draw_real_box("🔥 국내 커뮤니티 최신 (인벤 등)", df[df['category'] == '커뮤니티'])
