import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time

# 1. 페이지 설정 및 프리텐다드 CDN
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

# 2. 고도화된 스타일링 (피드백 반영)
st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
<style>
    /* 전체 배경 및 폰트 */
    body, .stApp { font-family: "Pretendard Variable", sans-serif !important; background-color: #f2f2f2 !important; }
    @media (min-width: 1200px) { .block-container { max-width: 1100px !important; margin: auto !important; padding-top: 2rem !important; } }
    
    /* [피드백 1] 메인 로고 바 높이 조정 (반짤림 방지) */
    .main-logo-bar {
        background-color: #3e4156;
        padding: 16px; /* 높이 확보 */
        color: white;
        border-radius: 6px;
        margin-bottom: 20px;
        font-weight: 800;
        font-size: 24px; /* 폰트 크기 최적화 */
        text-align: center;
        line-height: 1.2; /* 자간 조정 */
        letter-spacing: -0.05em;
    }

    /* 섹션 타이틀 (AAGAG 오마주) */
    .section-bar { 
        background-color: #55587c; 
        color: white; 
        padding: 6px 12px; 
        font-size: 13px; 
        font-weight: 700; 
        border-radius: 4px 4px 0 0;
        letter-spacing: -0.03em;
    }

    /* 리스트 박스 커스텀 */
    .custom-box {
        background-color: white;
        border: 1px solid #ddd;
        border-top: none;
        margin-bottom: 18px;
        min-height: 250px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    /* 리스트 아이템 디자인 (썸네일/출처 포함) */
    .list-row {
        display: flex;
        padding: 8px 12px;
        border-bottom: 1px solid #f2f2f2;
        align-items: center;
        transition: background 0.1s;
    }
    .list-row:hover { background-color: #f9f9f9; }

    /* [피드백 4] 썸네일 이미지 박스 */
    .thumb-box {
        width: 38px; height: 38px;
        background-color: #eee;
        margin-right: 12px;
        border-radius: 4px;
        flex-shrink: 0;
        overflow: hidden;
    }
    .thumb-box img { width: 100%; height: 100%; object-fit: cover; }

    .content-area { flex-grow: 1; overflow: hidden; min-width: 0; }
    
    .title-text { 
        color: #333; font-weight: 600; font-size: 12.5px;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; 
        letter-spacing: -0.03em;
    }

    /* [피드백 3] 출처별 다른 색상 뱃지 */
    .source-tag {
        font-size: 10px; font-weight: 800;
        padding: 1px 4px; border-radius: 2px;
        margin-right: 8px; flex-shrink: 0;
    }
    .tag-naver { background-color: #e6f7ed; color: #10b981; } /* 네이버 초록색 */
    .tag-inven { background-color: #eef2ff; color: #4338ca; } /* 인벤 파란색 */
    .tag-biz { background-color: #fff1f2; color: #e11d48; }   /* 비즈니스 분홍색 */
    .tag-global { background-color: #fffbeb; color: #d97706; } /* 글로벌 주황색 */
    .tag-ruli { background-color: #f3f4f6; color: #6b7280; }  /* 루리웹 회색 */

    /* [피드백 2] 중간 안내 배너 (AAGAG와 동일하게 가독성 높임) */
    .mid-banner { 
        background-color: #e6f7ff; color: #1976d2; padding: 10px; 
        text-align: center; font-size: 13px; font-weight: bold; 
        margin: 15px 0; border-radius: 4px; border: 1px solid #b3e5fc;
    }

    /* 하단 랭킹 리스트 전용 */
    .rank-num { font-weight: 800; width: 22px; color: #adb5bd; margin-right: 10px; font-size: 14px; text-align: center; }
    .blue { color: #3b82f6 !important; } .red { color: #ef4444 !important; } .green { color: #10b981 !important; }
</style>
""", unsafe_allow_html=True)

# 3. 데이터 수집 엔진 (썸네일, 출처 색상, 자동번역 포함)
@st.cache_data(ttl=600)
def fetch_optimized_data():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}
    data = []
    seen = set()

    # 데이터 수집 타겟 (썸네일, 출처, 카테고리 포함)
    targets = [
        {"name": "지디넷", "cat": "비즈니스", "tag": "tag-biz"},
        {"name": "MTN", "cat": "비즈니스", "tag": "tag-biz"},
        {"name": "딜사이트", "cat": "비즈니스", "tag": "tag-biz"},
        {"name": "IGN", "cat": "해외매체", "tag": "tag-global", "translate": True},
        {"name": "VGC", "cat": "해외매체", "tag": "tag-global", "translate": True},
        {"name": "인벤", "cat": "커뮤니티", "tag": "tag-inven"},
        {"name": "루리웹", "cat": "커뮤니티", "tag": "tag-ruli"},
        {"name": "펨코", "cat": "커뮤니티", "tag": "tag-inven"} # 예시 태그
    ]

    # 샘플 이미지 URL (진짜 데이터 연동 전까지 구색 맞추기용)
    thumbs = [
        "https://via.placeholder.com/38?text=N", # 뉴스
        "https://via.placeholder.com/38?text=G", # 글로벌
        "https://via.placeholder.com/38?text=I"  # 인벤/커뮤니티
    ]

    # 데이터 생성 로직 (실제 수집 시 사이트 HTML 분석 필요)
    for site in targets:
        for i in range(7):
            title = f"{site['name']} 핵심 게임 산업 이슈 #{i+1}"
            if site.get("translate"): title = f"🌏 {site['name']} 글로벌 소식: 최신 트렌드 {i+1}"
            
            # 썸네일 매칭
            thumb = thumbs[0] if site['cat'] == '비즈니스' else thumbs[1] if site['cat'] == '해외매체' else thumbs[2]

            if title not in seen:
                data.append({
                    "title": title, "source": site['name'], "category": site['cat'], 
                    "tag_class": site['tag'], "thumb": thumb,
                    "views": 10000 - (i*1000), "likes": 500 - (i*50), "cmts": 100 - (i*10), "time": i*10
                })
                seen.add(title)
    
    return pd.DataFrame(data)

df = fetch_optimized_data()

# --- 화면 렌더링 ---
st.markdown('<div class="main-logo-bar">AAGIG: Game Insight Ground</div>', unsafe_allow_html=True)

# 4. 상단 섹션 (4분할 그리드)
c1, c2 = st.columns(2)

def draw_grid_box(col, header, data_subset):
    with col:
        st.markdown(f'<div class="section-bar"><span>{header}</span><span style="font-weight:400; font-size:11px;">더 보기</span></div>', unsafe_allow_html=True)
        html = '<div class="custom-box">'
        for _, r in data_subset.head(7).iterrows():
            html += f"""
                <div class="list-row">
                    <div class="thumb-box"><img src="{r['thumb']}" alt="G"></div>
                    <div class="content-area">
                        <div class="title-text">{r['title']}</div>
                        <span class="source-tag {r['tag_class']}">{r['source']}</span>
                        <span style="font-size:10px; color:#aaa;">👁️ {r['views']} | 💬 {r['cmts']} | {r['time']}분전</span>
                    </div>
                </div>
            """
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

with c1: draw_grid_box(c1, "📊 최신 이슈 모음", df)
with c2: draw_grid_box(c2, "🔥 3시간 내 핫이슈 모음", df[df['time'] <= 180].sort_values('views', ascending=False))
with c1: draw_grid_box(c1, "🕘 9시간 내 핫이슈 모음", df[df['time'] <= 540].sort_values('views', ascending=False))
with c2: draw_grid_box(c2, "❤️ 24시간 내 가장 많이 하트 받은 이슈", df.sort_values('likes', ascending=False))

# [피드백 2] 중간 배너 (로그인 기능 삭제)
st.markdown('<div class="mid-banner">실시간 게임 산업 인사이트 통합 그라운드 | AAGIG Mirroring</div>', unsafe_allow_html=True)

# 5. 하단 섹션 (3분할 랭킹)
b1, b2, b3 = st.columns(3)

def draw_rank_box(col, header, data_subset, score_col, color_class):
    with col:
        st.markdown(f'<div class="section-bar"><span>{header}</span><span style="font-weight:400; font-size:11px;">더 보기</span></div>', unsafe_allow_html=True)
        html = '<div class="custom-box">'
        for i, (_, r) in enumerate(data_subset.head(20).iterrows()):
            num = i + 1
            num_class = color_class if num <= 5 else ""
            html += f"""
                <div class="list-row">
                    <span class="rank-num {num_class}">{num}</span>
                    <div class="content-area">
                        <div class="title-text">{r['title']}</div>
                        <span class="source-tag {r['tag_class']}">{r['source']}</span>
                    </div>
                    <span style="font-size:10px; color:#bbb; min-width:30px; text-align:right;">{r[score_col]}</span>
                </div>
            """
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

draw_rank_box(b1, "커뮤니티 인기순 (조회수)", df.sort_values('views', ascending=False), 'views', "blue")
draw_rank_box(b2, "가장 많이 읽은 순서 (하트)", df.sort_values('likes', ascending=False), 'likes', "red")
draw_rank_box(b3, "커뮤니티 댓글순 (Comments)", df.sort_values('cmts', ascending=False), 'cmts', "green")
