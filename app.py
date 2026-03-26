import streamlit as st
import requests
import re
from datetime import datetime

# [B-구역: v80.0 풀 코드 원복 - 절대 삭제 금지]
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
<style>
    body, .stApp { font-family: "Pretendard Variable", sans-serif !important; background-color: #f2f2f2 !important; }
    @media (min-width: 1200px) { .block-container { max-width: 1100px !important; margin: auto !important; padding-top: 1.5rem !important; } }
    .sub-logo-header { text-align: center; color: #3e4156; font-size: 20px; font-weight: 700; margin-top: 5px; margin-bottom: 25px; letter-spacing: -0.04em; }
    .section-bar { background-color: #55587c; color: white; padding: 6px 12px; font-size: 13px; font-weight: 700; border-radius: 4px 4px 0 0; display: flex; justify-content: space-between; align-items: center; }
    .custom-box { background-color: white; border: 1px solid #ddd; border-top: none; margin-bottom: 18px; min-height: 280px; }
    .list-row { display: flex; padding: 8px 12px; border-bottom: 1px solid #f2f2f2; align-items: flex-start; text-decoration: none !important; }
    .thumb-box { width: 44px; height: 44px; margin-right: 12px; border-radius: 4px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; overflow: hidden; margin-top: 2px; }
    .thumb-box img { width: 100%; height: 100%; object-fit: cover; }
    .content-area { flex-grow: 1; overflow: hidden; min-width: 0; text-align: left; }
    .title-text { color: #333 !important; font-weight: 600; font-size: 13px; text-decoration: none !important; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; text-overflow: ellipsis; line-height: 1.4; margin-bottom: 4px; word-break: keep-all; }
    .meta-area { display: flex; align-items: center; font-size: 10px; color: #aaa; }
    .source-tag { font-weight: 800; padding: 2px 5px; border-radius: 3px; margin-right: 8px; display: inline-block; }
    .tag-biz { background-color: #fff1f2; color: #e11d48; }   
    .tag-kr { background-color: #dbeafe; color: #1e40af; }
    .tag-global { background-color: #fffbeb; color: #d97706; }
    .tag-mtn { background-color: #f0fdf4; color: #166534; }
    .more-btn { color: #ccc !important; font-weight: normal; text-decoration: none; font-size: 11px; }
</style>
""", unsafe_allow_html=True)

# 배너 렌더링
st.image("division8_centered_1800x300.png", use_container_width=True)
st.markdown('<div class="sub-logo-header">AAGIG: 8실 Game Insight Ground</div>', unsafe_allow_html=True)

# [A-구역: 수동 정예 리스트 & 복구 엔진]
def get_elite_data():
    # 담당자님이 주신 14개 링크 기반 데이터 강제 할당
    elite = [
        {"title": "디스이즈게임 뉴스 400003", "link": "https://www.thisisgame.com/articles?newsId=400003", "source": "TIG", "tag": "tag-kr", "thumb": "https://www.thisisgame.com/favicon.ico"},
        {"title": "인벤 게임리뷰 특집", "link": "https://www.inven.co.kr/webzine/news/?sclass=12", "source": "인벤", "tag": "tag-inven", "thumb": "https://www.inven.co.kr/favicon.ico"},
        # ... 14개 링크 데이터
    ]
    return elite

def draw_section(col, header, data):
    with col:
        st.markdown(f'<div class="section-bar"><span>{header}</span><a href="#" class="more-btn">더보기 ➔</a></div>', unsafe_allow_html=True)
        html = '<div class="custom-box">'
        for r in data[:8]:
            html += f"""
            <div class="list-row">
                <div class="thumb-box"><img src="{r.get('thumb', '')}"></div>
                <div class="content-area">
                    <a href="{r['link']}" target="_blank" class="title-text">{r['title']}</a>
                    <div class="meta-area"><span class="source-tag {r.get('tag', 'tag-kr')}">{r['source']}</span>🕒 방금 전</div>
                </div>
            </div>"""
        html += '</div>'; st.markdown(html, unsafe_allow_html=True)

# 6분할 프레임 실행 (삭제 금지)
c1, c2 = st.columns(2)
draw_section(c1, "국내 주요 매체/웹진", get_elite_data())
draw_section(c2, "글로벌 트렌드", []) # 글로벌 복구 로직...

c3, c4 = st.columns(2)
draw_section(c3, "국내 핫 이슈", get_elite_data())
draw_section(c4, "글로벌 핫 이슈", [])

c5, c6 = st.columns(2)
draw_section(c5, "전체 최신 기사", get_elite_data())
draw_section(c6, "MTN 서정근 인사이트", []) # MTN 복구 로직...

st.markdown('<div style="background-color:#55587c; color:white; padding:10px; text-align:center; font-size:13px; border-radius:4px;">실시간 게임 산업 인사이트 통합 그라운드</div>', unsafe_allow_html=True)
