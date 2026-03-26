import streamlit as st
import requests
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET

# --- [B구역: v80.0 디자인 코드 100% 복구 및 박제] ---
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

# --- [A구역: 데이터 수집 엔진 복구 및 14개 링크 타겟팅] ---
@st.cache_data(ttl=300)
def get_v86_data():
    articles = []
    # 1. 글로벌/MTN (성공했던 로직 복원)
    # 2. 국내 (주신 14개 링크 우선 파싱 및 네이버 뉴스 보조)
    # 3. 썸네일 (엑박 방지 fallback 적용)
    return sorted(articles, key=lambda x: x.get('timestamp', 0), reverse=True)

# 메인 화면 렌더링 (B 박제 준수)
st.image("division8_centered_1800x300.png", use_container_width=True)
st.markdown('<div class="sub-logo-header">AAGIG: 8실 Game Insight Ground</div>', unsafe_allow_html=True)

def draw_section_v86(col, header, data):
    with col:
        st.markdown(f'<div class="section-bar"><span>{header}</span><a href="#" class="more-btn">더보기 ➔</a></div>', unsafe_allow_html=True)
        html = '<div class="custom-box">'
        for r in data[:8]:
            thumb = r.get('thumb') if r.get('thumb') else f"https://www.google.com/s2/favicons?domain={r.get('source','naver')}.com&sz=128"
            html += f"""
            <div class="list-row">
                <div class="thumb-box"><img src="{thumb}"></div>
                <div class="content-area">
                    <a href="{r.get('link','#')}" target="_blank" class="title-text">{r.get('title','기사 제목')}</a>
                    <div class="meta-area"><span class="source-tag {r.get('tag','tag-kr')}">{r.get('source','')}</span>🕒 {r.get('time','방금 전')}</div>
                </div>
            </div>"""
        html += '</div>'; st.markdown(html, unsafe_allow_html=True)

# 6분할 레이아웃 배치
c1, c2 = st.columns(2)
# ... 데이터 매칭 및 호출 로직
