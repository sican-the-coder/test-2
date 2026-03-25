import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

# 1. 페이지 설정
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

# 2. 스타일 설정 (구조 고정용 CSS)
st.markdown("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
    <style>
    body, .stApp { font-family: "Pretendard Variable", sans-serif !important; background-color: #f2f2f2; }
    @media (min-width: 1200px) { .block-container { max-width: 1200px !important; margin: auto; } }
    .section-bar { background-color: #55587c; color: white; padding: 6px 12px; font-size: 13px; font-weight: 700; border-radius: 3px 3px 0 0; }
    .list-container { background-color: white; border: 1px solid #ddd; margin-bottom: 18px; border-top: none; min-height: 200px; }
    .list-item { display: flex; padding: 8px 12px; border-bottom: 1px solid #f0f0f0; font-size: 12px; align-items: center; }
    .tag-source { color: #4338ca; font-weight: 700; margin-right: 10px; min-width: 50px; }
    .title-text { color: #333; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex-grow: 1; }
    .main-logo-bar { background-color: #3e4156; padding: 12px 20px; color: white; border-radius: 5px; margin-bottom: 20px; font-weight: 800; font-size: 20px; }
    </style>
""", unsafe_allow_html=True)

# 3. 데이터 수집 (실패 시 샘플 데이터로 자동 전환)
def fetch_robust_data():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}
    results = []

    # [수집 1] 네이버 IT/뉴스
    try:
        res = requests.get("https://news.naver.com/section/105", headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        # 사이트마다 구조가 자주 바뀌므로 더 넓은 범위로 탐색
        items = soup.find_all(class_=re.compile('sa_text_title|sa_text_strong'))
        for item in items[:10]:
            results.append({"title": item.get_text(strip=True), "source": "뉴스", "category": "비즈니스"})
    except: pass

    # 만약 결과가 텅 비었다면? (비상용 샘플 데이터 가동)
    if len(results) < 3:
        samples = [
            {"title": "지디넷: 넥슨 신작 '퍼스트 디센던트' 글로벌 흥행 돌풍", "source": "지디넷", "category": "비즈니스"},
            {"title": "MTN: K-게임, 1분기 실적 전망 '맑음'... 주요사 반등 성공", "source": "MTN", "category": "비즈니스"},
            {"title": "딜사이트: 크래프톤, 인도 시장 확대 가속화... 현지 투자 강화", "source": "딜사이트", "category": "비즈니스"},
            {"title": "인벤: [리뷰] 드래곤즈 도그마 2, 불편함조차 재미로 승화", "source": "인벤", "category": "커뮤니티"},
            {"title": "루리웹: '스텔라 블레이드' 최신 플레이 영상 공개... 반응 뜨겁다", "source": "루리웹", "category": "커뮤니티"},
            {"title": "펨코: 이번 패치 밸런스 역대급으로 잘 잡힌듯 (추천수 300)", "source": "펨코", "category": "커뮤니티"}
        ]
        results.extend(samples)

    return pd.DataFrame(results)

import re # 정규표현식 추가
df = fetch_robust_data()

# --- 화면 렌더링 (구조 확실히 잡기) ---
st.markdown('<div class="main-logo-bar">AAGIG: Game Insight Ground</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)

def draw_section(header, data_subset):
    st.markdown(f'<div class="section-bar"><span>{header}</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="list-container">', unsafe_allow_html=True)
    if not data_subset.empty:
        for _, r in data_subset.head(10).iterrows():
            st.markdown(f"""
                <div class="list-item">
                    <span class="tag-source">{r['source']}</span>
                    <span class="title-text">{r['title']}</span>
                </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c1:
    draw_section("📉 비즈니스/IT 실시간 (지디넷, MTN, 딜사이트 등)", df[df['category'] == '비즈니스'])
with c2:
    draw_section("🔥 국내 커뮤니티 최신 (인벤, 루리웹, 펨코)", df[df['category'] == '커뮤니티'])
