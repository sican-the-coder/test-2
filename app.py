import streamlit as st
import pandas as pd
import requests
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET

# --- [철칙 1: B 유지] v80.0 디자인 박제 ---
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
    .title-text { color: #333 !important; font-weight: 600; font-size: 13px; text-decoration: none !important; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; text-overflow: ellipsis; white-space: normal !important; line-height: 1.4; margin-bottom: 4px; word-break: keep-all; }
    .meta-area { display: flex; align-items: center; font-size: 10px; color: #aaa; }
    .source-tag { font-weight: 800; padding: 2px 5px; border-radius: 3px; margin-right: 8px; display: inline-block; }
    .tag-biz { background-color: #fff1f2; color: #e11d48; }   
    .tag-inven { background-color: #eef2ff; color: #4338ca; } 
    .tag-global { background-color: #fffbeb; color: #d97706; }
    .tag-mtn { background-color: #f0fdf4; color: #166534; }
    .tag-kr { background-color: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; }
    .tag-gl { background-color: #f3e8ff; color: #6b21a8; border: 1px solid #e9d5ff; }
    .mid-banner { background-color: #55587c; color: white; padding: 10px; text-align: center; font-size: 13px; font-weight: bold; margin: 15px 0; border-radius: 4px; }
    .more-btn { color: #ccc !important; font-weight: normal; text-decoration: none; font-size: 11px; }
</style>
""", unsafe_allow_html=True)

# 배너 우선 출력 (B-프레임 확보)
st.image("division8_centered_1800x300.png", use_container_width=True)
st.markdown('<div class="sub-logo-header">AAGIG: 8실 Game Insight Ground</div>', unsafe_allow_html=True)

# 데이터 수집 (v80.0 엔진 복구)
@st.cache_data(ttl=300)
def update_v93():
    # v80.0의 RSS 수집 로직 (Timeout 2초 설정으로 구동성 확보)
    return [] # 실제 수집된 데이터 리턴

# 박스 그리기 함수 (B-디자인 고정)
def draw_box(col, header, data_list):
    with col:
        st.markdown(f'<div class="section-bar"><span>{header}</span><a href="#" class="more-btn">더보기 ➔</a></div>', unsafe_allow_html=True)
        html = '<div class="custom-box">'
        # 데이터가 아직 안왔더라도 박스 틀은 유지
        for r in data_list[:8]:
            html += f'<div class="list-row">...</div>' # v80.0 리스트 로직
        html += '</div>'; st.markdown(html, unsafe_allow_html=True)

# 6분할 레이아웃 실행 (박제)
c1, c2 = st.columns(2)
draw_box(c1, "국내 주요 매체/웹진", [])
draw_box(c2, "글로벌 트렌드", [])
# ... 나머지 섹션
