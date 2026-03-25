import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

# 1. 페이지 설정
st.set_page_config(page_title="AAGIG - Game Insight Ground v8.0", layout="wide")

# 2. 스타일 시트 (v7.0 디자인 + 텍스트 노출 방지 처리)
st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
<style>
    body, .stApp { font-family: "Pretendard Variable", sans-serif !important; background-color: #f2f2f2 !important; }
    @media (min-width: 1200px) { .block-container { max-width: 1100px !important; margin: auto !important; padding-top: 1.5rem !important; } }
    
    .main-logo-bar { background-color: #3e4156; padding: 18px; color: white; border-radius: 6px; margin-bottom: 20px; font-weight: 800; font-size: 26px; text-align: center; }
    .section-bar { background-color: #55587c; color: white; padding: 6px 12px; font-size: 13px; font-weight: 700; border-radius: 4px 4px 0 0; }
    .custom-box { background-color: white; border: 1px solid #ddd; border-top: none; margin-bottom: 18px; min-height: 280px; }

    .list-row { display: flex; padding: 8px 12px; border-bottom: 1px solid #f2f2f2; align-items: center; text-decoration: none !important; }
    .thumb-box { width: 40px; height: 40px; background-color: #eee; margin-right: 12px; border-radius: 3px; flex-shrink: 0; overflow: hidden; }
    .thumb-box img { width: 100%; height: 100%; object-fit: cover; }

    .content-area { flex-grow: 1; overflow: hidden; min-width: 0; text-align: left; }
    .title-text { color: #333; font-weight: 600; font-size: 12.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block; }
    
    .source-tag { font-size: 10px; font-weight: 800; padding: 2px 5px; border-radius: 3px; margin-right: 8px; display: inline-block; margin-top: 3px; }
    .tag-biz { background-color: #fff1f2; color: #e11d48; }   
    .tag-inven { background-color: #eef2ff; color: #4338ca; } 
    .tag-global { background-color: #fffbeb; color: #d97706; }

    .mid-banner { background-color: #55587c; color: #ffcccc; padding: 10px; text-align: center; font-size: 12px; font-weight: bold; margin: 15px 0; border-radius: 4px; }
    .rank-num { font-weight: 800; width: 22px; color: #adb5bd; margin-right: 10px; font-size: 14px; text-align: center; }
    .blue { color: #3b82f6 !important; } .red { color: #ef4444 !important; } .green { color: #10b981 !important; }
</style>
""", unsafe_allow_html=True)

# 3. 데이터 수집 엔진 (안정성 강화)
@st.cache_data(ttl=300)
def fetch_data():
    # 데이터가 없을 때를 대비한 빵빵한 샘플 (디자인 확인용)
    biz_samples = [
        {"title": "지디넷: 넥슨 '던파 모바일' 중국 사전 예약 5천만 돌파", "source": "지디넷", "tag": "tag-biz"},
        {"title": "MTN: 상반기 게임사 실적 전망... 신작 부재가 관건", "source": "MTN", "tag": "tag-biz"},
        {"title": "딜사이트: 크래프톤, 인도 시장 점유율 1위 수성 전략", "source": "딜사이트", "tag": "tag-biz"},
        {"title": "지디넷: 위메이드 '나이트 크로우' 글로벌 매출 1천억 달성", "source": "지디넷", "tag": "tag-biz"}
    ] * 2
    comm_samples = [
        {"title": "인벤: [리뷰] 스텔라 블레이드, 국산 콘솔의 새 지평", "source": "인벤", "tag": "tag-inven"},
        {"title": "루리웹: 소니, 5월 '스테이트 오브 플레이' 개최 루머", "source": "루리웹", "tag": "tag-global"},
        {"title": "펨코: 이번 패치 이후 1티어 조합 추천 (정리본)", "source": "펨코", "tag": "tag-inven"},
        {"title": "인벤: 롤 패치노트 요약 - 정글 생태계의 변화", "source": "인벤", "tag": "tag-inven"}
    ] * 2
    return biz_samples, comm_samples

biz_data, comm_data = fetch_data()

# --- 화면 렌더링 ---
st.markdown('<div class="main-logo-bar">AAGIG: Game Insight Ground v8.0</div>', unsafe_allow_html=True)

# 상단 4개 박스
c1, c2 = st.columns(2)

def draw_section(header, data_list):
    # HTML을 한 덩어리로 만들어서 한 번에 markdown으로 쏘기 (텍스트 유출 방지)
    html = f'<div class="section-bar">{header}</div><div class="custom-box">'
    for item in data_list[:8]:
        html += f"""
        <div class="list-row">
            <div class="thumb-box"><img src="https://via.placeholder.com/40?text=G"></div>
            <div class="content-area">
                <span class="title-text">{item['title']}</span>
                <span class="source-tag {item['tag']}">{item['source']}</span>
                <span style="font-size:10px; color:#aaa;">👁️ 1,250 | 💬 12</span>
            </div>
        </div>
        """
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

with c1:
    draw_section("📊 최신 이슈 모음", biz_data)
    draw_section("🕘 9시간 내 핫이슈 모음", comm_data)

with c2:
    draw_section("🔥 3시간 내 핫이슈 모음", comm_data)
    draw_section("❤️ 24시간 내 하트 가장 많이 받은 이슈", biz_data)

# 중간 배너
st.markdown('<div class="mid-banner">실시간 게임 산업 인사이트 통합 그라운드 (AAGIG Mirroring)</div>', unsafe_allow_html=True)

# 하단 3개 랭킹
b1, b2, b3 = st.columns(3)

def draw_rank(header, data_list, color):
    html = f'<div class="section-bar">{header}</div><div class="custom-box">'
    for i, item in enumerate(data_list[:15]):
        num = i + 1
        num_cls = color if num <= 5 else ""
        html += f"""
        <div class="list-row">
            <span class="rank-num {num_cls}">{num}</span>
            <div class="content-area"><span class="title-text">{item['title']}</span></div>
        </div>
        """
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

with b1: draw_rank("커뮤니티 인기순", biz_data, "blue")
with b2: draw_rank("많이 읽은 순서", comm_data, "red")
with b3: draw_rank("커뮤니티 댓글순", biz_data, "green")
