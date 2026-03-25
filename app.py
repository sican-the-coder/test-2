import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

# 1. 페이지 설정
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

# 2. 스타일 설정 (프리텐다드 + AAGAG UI 복원)
st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
<style>
    body, .stApp { font-family: "Pretendard Variable", sans-serif !important; background-color: #f2f2f2 !important; }
    @media (min-width: 1200px) { .block-container { max-width: 1100px !important; margin: auto !important; padding-top: 1rem !important; } }
    
    .main-logo-bar { background-color: #3e4156; padding: 12px; color: white; border-radius: 4px; margin-bottom: 15px; font-weight: 800; font-size: 20px; text-align: center; }
    .section-bar { background-color: #55587c; color: white; padding: 6px 12px; font-size: 13px; font-weight: 700; border-radius: 3px 3px 0 0; }
    .custom-box { background-color: white; border: 1px solid #ddd; border-top: none; margin-bottom: 15px; min-height: 250px; }
    .list-row { display: flex; padding: 6px 12px; border-bottom: 1px solid #f2f2f2; align-items: center; font-size: 12px; }
    .tag-source { color: #4338ca; font-weight: 800; min-width: 50px; font-size: 10px; margin-right: 8px; }
    .text-content { color: #333; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex-grow: 1; }
    .rank-num { font-weight: 800; width: 20px; color: #adb5bd; margin-right: 10px; font-size: 13px; text-align: center; }
    .blue { color: #3b82f6 !important; } .red { color: #ef4444 !important; } .green { color: #10b981 !important; }
    .login-banner { background-color: #55587c; color: #ffcccc; padding: 8px; text-align: center; font-size: 12px; font-weight: bold; margin: 15px 0; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# 3. 실시간 데이터 수집 (안정성 강화)
def fetch_real_data():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}
    data = []
    seen = set()

    # [수집] 뉴스 & 커뮤니티 통합 수집 시도
    targets = [
        ("https://news.naver.com/section/105", "뉴스", "비즈니스"),
        ("https://www.inven.co.kr/webzine/news/", "인벤", "커뮤니티")
    ]

    for url, src, cat in targets:
        try:
            res = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(res.text, 'html.parser')
            # 네이버용/인벤용 선택자 통합
            items = soup.select('.sa_text_title, .sa_text_strong, .newsList .info .title')
            for t in items:
                txt = t.get_text(strip=True)
                if txt not in seen:
                    data.append({"title": txt, "source": src, "category": cat, "val": 100})
                    seen.add(txt)
        except: pass

    # 데이터 부족 시 가짜 데이터 보충
    if len(data) < 10:
        for i in range(10):
            data.append({"title": f"실시간 게임 산업 분석 리포트 이슈 {i+1}", "source": "AAGIG", "category": "비즈니스", "val": 50})
    
    return pd.DataFrame(data)

df = fetch_real_data()

# --- 화면 구성 시작 ---
st.markdown('<div class="main-logo-bar">AAGIG: Game Insight Ground</div>', unsafe_allow_html=True)

# 상단 4분할 격자
c1, c2 = st.columns(2)

def draw_grid_box(col, header, data_subset):
    with col:
        st.markdown(f'<div class="section-bar">{header}</div>', unsafe_allow_html=True)
        html = '<div class="custom-box">'
        for _, r in data_subset.head(7).iterrows():
            html += f'<div class="list-row"><span class="tag-source">{r["source"]}</span><span class="text-content">{r["title"]}</span></div>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

draw_grid_box(c1, "📊 최신 이슈 모음", df)
draw_grid_box(c2, "🔥 3시간 내 핫이슈 모음", df.iloc[::-1]) # 예시로 반전 데이터
draw_grid_box(c1, "🕘 9시간 내 핫이슈 모음", df.sample(frac=1))
draw_grid_box(c2, "❤️ 24시간 내 가장 많이 받은 하트", df.sort_values('val'))

# 중간 배너
st.markdown('<div class="login-banner">로그인을 하시면 커뮤니티 리스트를 편집가능합니다. (AAGIG Mirroring)</div>', unsafe_allow_html=True)

# 하단 3분할 랭킹
b1, b2, b3 = st.columns(3)

def draw_rank_box(col, header, data_subset, color):
    with col:
        st.markdown(f'<div class="section-bar">{header}</div>', unsafe_allow_html=True)
        html = '<div class="custom-box">'
        for i, (_, r) in enumerate(data_subset.head(15).iterrows()):
            num = i + 1
            num_class = color if num <= 5 else ""
            html += f'<div class="list-row"><span class="rank-num {num_class}">{num}</span><span class="text-content">{r["title"]}</span></div>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

draw_rank_box(b1, "커뮤니티별 인기순", df, "blue")
draw_rank_box(b2, "많이 읽은 순서", df, "red")
draw_rank_box(b3, "커뮤니티별 댓글순", df, "green")
