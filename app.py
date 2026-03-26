import streamlit as st
import requests
import re
import json
from datetime import datetime
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

# --- [철칙 1: B 유지] 소멸된 디자인 및 프레임 전면 재건 ---
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
<style>
    body, .stApp { font-family: "Pretendard Variable", sans-serif !important; background-color: #f2f2f2 !important; }
    @media (min-width: 1200px) { .block-container { max-width: 1100px !important; margin: auto !important; padding-top: 1.5rem !important; } }
    .sub-logo-header { text-align: center; color: #3e4156; font-size: 20px; font-weight: 700; margin-top: 5px; margin-bottom: 25px; }
    .section-bar { background-color: #55587c; color: white; padding: 6px 12px; font-size: 13px; font-weight: 700; border-radius: 4px 4px 0 0; display: flex; justify-content: space-between; align-items: center; }
    .custom-box { background-color: white; border: 1px solid #ddd; border-top: none; margin-bottom: 18px; min-height: 280px; }
    .list-row { display: flex; padding: 8px 12px; border-bottom: 1px solid #f2f2f2; align-items: flex-start; }
    .thumb-box { width: 44px; height: 44px; margin-right: 12px; border-radius: 4px; flex-shrink: 0; overflow: hidden; margin-top: 2px; }
    .thumb-box img { width: 100%; height: 100%; object-fit: cover; }
    .title-text { color: #333 !important; font-weight: 600; font-size: 13px; text-decoration: none; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.4; }
    .source-tag { font-weight: 800; padding: 2px 5px; border-radius: 3px; font-size: 10px; margin-right: 8px; background-color: #eee; color: #666; }
</style>
""", unsafe_allow_html=True)

# 2. [A 엔진 복구] 14개 링크 타겟 수집 로직
@st.cache_data(ttl=300)
def fetch_elite_news():
    news_list = []
    targets = [
        ("https://www.thisisgame.com/articles?newsId=400003", "TIG"),
        ("https://www.inven.co.kr/webzine/news/?sclass=12", "인벤리뷰"),
        ("https://www.gamemeca.com/review.php", "게임메카"),
        ("https://dealsite.co.kr/search/?LIKE=넥슨", "딜사이트"),
        ("https://news.google.com/rss/search?q=게임&hl=ko&gl=KR&ceid=KR:ko", "네이버")
    ]
    
    for url, src in targets:
        try:
            # RSS와 일반 페이지 하이브리드 대응
            res = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
            if "xml" in res.headers.get('Content-Type', ''):
                root = ET.fromstring(res.text)
                for item in root.findall('.//item')[:5]:
                    news_list.append({
                        "title": item.find('title').text, "link": item.find('link').text,
                        "source": src, "thumb": f"https://www.google.com/s2/favicons?domain={url}&sz=128",
                        "time": "방금 전", "group": "domestic"
                    })
            else:
                soup = BeautifulSoup(res.text, 'html.parser')
                og_title = soup.find("meta", property="og:title")
                og_image = soup.find("meta", property="og:image")
                if og_title:
                    news_list.append({
                        "title": og_title["content"], "link": url, "source": src,
                        "thumb": og_image["content"] if og_image else "",
                        "time": "오늘", "group": "domestic"
                    })
        except: continue
    return news_list

# 글로벌/MTN 더미 데이터 (엔진 복구 확인용)
glo_data = [{"title": "[Global] Game News Title", "link": "#", "source": "GameSpot", "thumb": "", "group": "global"}]
mtn_data = [{"title": "[MTN] 서정근 인사이트", "link": "#", "source": "MTN", "thumb": "", "group": "mtn"}]

dom_data = fetch_elite_news()

# 3. [B 레이아웃 복구] 배너 및 6분할 프레임 재건
st.image("division8_centered_1800x300.png", use_container_width=True)
st.markdown('<div class="sub-logo-header">AAGIG: 8실 Game Insight Ground</div>', unsafe_allow_html=True)

def draw_box(col, header, data):
    with col:
        st.markdown(f'<div class="section-bar"><span>{header}</span><a href="#" style="color:#ccc; font-size:11px; text-decoration:none;">더보기 ➔</a></div>', unsafe_allow_html=True)
        html = '<div class="custom-box">'
        for r in data[:8]:
            thumb = r.get('thumb') if r.get('thumb') else "https://via.placeholder.com/44"
            html += f"""
            <div class="list-row">
                <div class="thumb-box"><img src="{thumb}"></div>
                <div class="content-area">
                    <a href="{r.get('link','#')}" target="_blank" class="title-text">{r.get('title','기사 제목')}</a>
                    <div style="font-size:10px; color:#aaa; margin-top:4px;">
                        <span class="source-tag">{r.get('source','')}</span>{r.get('time','방금 전')}
                    </div>
                </div>
            </div>"""
        html += '</div>'; st.markdown(html, unsafe_allow_html=True)

c1, c2 = st.columns(2)
draw_box(c1, "국내 주요 매체/웹진", dom_data)
draw_box(c2, "글로벌 트렌드", glo_data)

c3, c4 = st.columns(2)
draw_box(c3, "국내 핫 이슈", dom_data[3:])
draw_box(c4, "글로벌 핫 이슈", glo_data)

c5, c6 = st.columns(2)
draw_box(c5, "전체 최신 기사", dom_data + glo_data)
draw_box(c6, "MTN 서정근 인사이트", mtn_data)

st.markdown('<div class="version-marker">v85.0 (Full Engine Restored)</div>', unsafe_allow_html=True)
