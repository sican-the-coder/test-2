import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

# 1. 페이지 설정 및 타이틀 (AAGIG 로고 스타일)
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

# 2. 모바일 대응 및 AAGIG UI 재현 CSS
st.markdown("""
    <style>
    /* 전체 배경 및 기본 폰트 */
    .stApp { background-color: #f2f2f2; }
    
    /* 헤더 스타일 */
    .main-title { 
        color: #55587c; font-size: 28px; font-weight: 800; text-align: center; 
        margin-bottom: 20px; font-family: 'Arial Black', sans-serif;
    }
    
    /* 섹션 헤더 */
    .section-header { 
        background-color: #55587c; color: white; padding: 8px 12px; 
        font-weight: bold; font-size: 13px; display: flex; justify-content: space-between;
        border-radius: 2px 2px 0 0;
    }

    /* 카드 박스 (모바일 대응을 위한 Flex/Grid) */
    .card-container { 
        background-color: white; border: 1px solid #ddd; margin-bottom: 15px; 
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .card-item { display: flex; padding: 8px; border-bottom: 1px solid #eee; }
    .card-thumb { 
        width: 45px; height: 45px; background-color: #eee; margin-right: 10px; 
        border-radius: 3px; flex-shrink: 0; overflow: hidden; 
    }
    .card-content { flex-grow: 1; overflow: hidden; min-width: 0; }
    .card-title { 
        font-weight: bold; color: #333; font-size: 12px; 
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; 
    }
    .card-meta { font-size: 10px; color: #888; margin-top: 3px; }

    /* 하단 랭킹 리스트 스타일 */
    .rank-item { display: flex; padding: 6px 10px; border-bottom: 1px solid #eee; font-size: 12px; align-items: center; }
    .rank-num { font-weight: bold; width: 22px; text-align: center; margin-right: 8px; font-size: 13px; color: #888; }
    .rank-title { flex-grow: 1; color: #444; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .rank-score { font-size: 10px; color: #aaa; width: 35px; text-align: right; }
    
    /* 뱃지 컬러 */
    .blue-num { color: #3498db !important; }
    .red-num { color: #e74c3c !important; }
    .green-num { color: #27ae60 !important; }

    /* 로그인 배너 (AAGAG 오마주) */
    .login-banner { 
        background-color: #55587c; color: #ffcccc; padding: 10px; 
        text-align: center; font-size: 12px; font-weight: bold; margin: 15px 0; border-radius: 3px;
    }

    /* 모바일에서 여백 조정 */
    @media (max-width: 768px) {
        .main-title { font-size: 22px; }
        .card-title { font-size: 13px; }
    }
    </style>
""", unsafe_allow_html=True)

# 3. 가상 데이터 생성 (실제 크롤링 로직으로 교체 가능)
def get_aagig_data():
    data = []
    # 최신이슈, 3h, 9h, 24h 구분을 위한 샘플 생성
    for i in range(50):
        data.append({
            "title": f"[{['공지','핫','뉴스','제보'][i%4]}] 게임 사업부 일간 리포트 이슈 {i+1}번 게시글입니다.",
            "comm": ["인벤", "디시", "공카", "루리웹"][i%4],
            "views": 1000 + (i * 250),
            "cmts": 10 + (i * 5),
            "likes": 5 + (i * 3),
            "time": i * 15 # 분 전
        })
    return pd.DataFrame(data)

df = get_aagig_data()

# --- 화면 구성 ---
st.markdown('<div class="main-title">📊 AAGIG (Game Insight Ground)</div>', unsafe_allow_html=True)

# 상단 4분할 섹션 (PC에선 2x2, 모바일에선 1x4 자동 전환)
col1, col2 = st.columns([1, 1])

def render_section(header, items):
    st.markdown(f'<div class="section-header"><span>{header}</span><span style="font-size:10px;">더 보기</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    for _, r in items.head(6).iterrows():
        st.markdown(f"""
            <div class="card-item">
                <div class="card-thumb"><img src="https://via.placeholder.com/45?text=G" style="width:100%;"></div>
                <div class="card-content">
                    <div class="card-title">{r['title']}</div>
                    <div class="card-meta">0.2MB | 👁️ {r['views']} | 💬 {r['cmts']} | 🕓 {r['time']}분전</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col1:
    render_section("최신 이슈 모음", df.sort_values('time'))
    render_section("9 시간 내 핫이슈 모음", df[df['time'] <= 540].sort_values('views', ascending=False))

with col2:
    render_section("3 시간 내 핫이슈 모음", df[df['time'] <= 180].sort_values('views', ascending=False))
    render_section("24 시간 내 하트 많이 받은 이슈", df.sort_values('likes', ascending=False))

# 중간 배너
st.markdown('<div class="login-banner">로그인을 하시면 커뮤니티 리스트를 편집가능합니다. (AAGIG Mirroring)</div>', unsafe_allow_html=True)

# 하단 3분할 랭킹 (PC 3열, 모바일 1열 자동 전환)
b1, b2, b3 = st.columns([1, 1, 1])

def render_rank(header, items, score_col, color_class):
    st.markdown(f'<div class="section-header"><span>{header}</span><span style="font-size:10px;">더 보기</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    for i, r in enumerate(items.head(15).iterrows()):
        num = i + 1
        st.markdown(f"""
            <div class="rank-item">
                <span class="rank-num {color_class if num <= 5 else ''}">{num}</span>
                <span class="rank-title">{r[1]['title']}</span>
                <span class="rank-score">{r[1][score_col]}</span>
            </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with b1: render_rank("커뮤니티별 인기순", df.sort_values('views', ascending=False), 'views', 'blue-num')
with b2: render_rank("가장 많이 읽은 순서", df.sort_values('likes', ascending=False), 'likes', 'red-num')
with b3: render_rank("커뮤니티별 댓글순", df.sort_values('cmts', ascending=False), 'cmts', 'green-num')

# 하단 툴바
st.divider()
st.caption("AAGIG UI Clone for Game Insight | Developed by Sican-the-coder")
