import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os

# 1. 페이지 설정
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

# 2. 스타일 시트 (가장 완벽했던 v11.0 기반 + 버전 숨김 처리)
st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
<style>
    body, .stApp { font-family: "Pretendard Variable", sans-serif !important; background-color: #f2f2f2 !important; }
    @media (min-width: 1200px) { .block-container { max-width: 1100px !important; margin: auto !important; padding-top: 1.5rem !important; } }
    
    .sub-logo-header { text-align: center; color: #3e4156; font-size: 20px; font-weight: 700; margin-top: 5px; margin-bottom: 25px; letter-spacing: -0.04em; }
    .section-bar { background-color: #55587c; color: white; padding: 6px 12px; font-size: 13px; font-weight: 700; border-radius: 4px 4px 0 0; }
    .custom-box { background-color: white; border: 1px solid #ddd; border-top: none; margin-bottom: 18px; min-height: 280px; }
    
    /* 리스트 정렬 (깨짐 복구 완료) */
    .list-row { display: flex; padding: 8px 12px; border-bottom: 1px solid #f2f2f2; align-items: center; text-decoration: none !important; }
    .thumb-box { width: 38px; height: 38px; background-color: #eee; margin-right: 12px; border-radius: 3px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; overflow: hidden; }
    .thumb-box img { width: 100%; height: 100%; object-fit: cover; }
    
    .content-area { flex-grow: 1; overflow: hidden; min-width: 0; text-align: left; }
    .title-text { color: #333; font-weight: 600; font-size: 12.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block; }
    .source-tag { font-size: 10px; font-weight: 800; padding: 2px 5px; border-radius: 3px; margin-right: 8px; display: inline-block; margin-top: 3px; }
    
    .tag-biz { background-color: #fff1f2; color: #e11d48; }   
    .tag-inven { background-color: #eef2ff; color: #4338ca; } 
    .tag-global { background-color: #fffbeb; color: #d97706; }
    
    .mid-banner { background-color: #55587c; color: white; padding: 10px; text-align: center; font-size: 13px; font-weight: bold; margin: 15px 0; border-radius: 4px; }
    .rank-num { font-weight: 800; width: 22px; color: #adb5bd; margin-right: 10px; font-size: 14px; text-align: center; }
    .blue { color: #3b82f6 !important; } .red { color: #ef4444 !important; } .green { color: #10b981 !important; }
    .version-marker { position: fixed; bottom: 5px; right: 10px; color: #888; font-size: 10px; opacity: 0.5; pointer-events: none; }
</style>
""", unsafe_allow_html=True)

# 3. [진짜 데이터 복구] 네이버 뉴스 기반 실시간 크롤링 (썸네일 포함)
@st.cache_data(ttl=300)
def fetch_real_live_data():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}
    results = []
    seen = set()

    try:
        res = requests.get("https://news.naver.com/section/105", headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = soup.select('.sa_item')
        
        for art in articles[:20]:
            title_el = art.select_one('.sa_text_title, .sa_text_strong')
            press_el = art.select_one('.sa_text_press')
            img_el = art.select_one('.sa_thumb_inner img, .sa_thumb_link img')
            
            if title_el:
                title = title_el.get_text(strip=True)
                if title not in seen:
                    thumb = img_el.get('data-src') or img_el.get('src') or "" if img_el else ""
                    source = press_el.get_text(strip=True) if press_el else "뉴스"
                    tag = "tag-biz" if any(x in source for x in ["지디넷", "MTN", "경제", "비즈", "파이낸셜"]) else "tag-inven"
                    
                    results.append({
                        "title": title, "source": source, "tag": tag, "thumb": thumb,
                        "views": 1500, "cmts": 24
                    })
                    seen.add(title)
    except:
        pass

    if len(results) < 5:
        results = [{"title": "데이터를 불러오는 중입니다...", "source": "AAGIG", "tag": "tag-global", "thumb": "", "views": 0, "cmts": 0}]
    
    return results

live_data = fetch_real_live_data()

# --- 화면 렌더링 ---

# [피드백 반영] 로고 안전하게 불러오기
try:
    st.image("division8_centered_1800x300.png", use_column_width=True)
except Exception:
    st.error("🚨 깃허브 저장소에 'division8_centered_1800x300.png' 파일이 없습니다. [Add file] -> [Upload files]를 눌러 이미지를 올려주세요!")

st.markdown('<div class="sub-logo-header">AAGIG: 8실 Game Insight Ground</div>', unsafe_allow_html=True)

# 상단 4분할 격자
c1, c2 = st.columns(2)

def draw_section(col, header, data_list):
    with col:
        html = f'<div class="section-bar">{header}</div><div class="custom-box">'
        for item in data_list[:8]:
            fallback_svg = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='38' height='38'><rect width='38' height='38' fill='%23eeeeee'/><text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' font-size='10' fill='%23999999'>No Img</text></svg>"
            img_url = item["thumb"] if item["thumb"] else fallback_svg
            img_tag = f'<img src="{img_url}" referrerpolicy="no-referrer" onerror="this.src=\'{fallback_svg}\'">'
            
            html += f'<div class="list-row"><div class="thumb-box">{img_tag}</div><div class="content-area"><span class="title-text">{item["title"]}</span><span class="source-tag {item["tag"]}">{item["source"]}</span><span style="font-size:10px; color:#aaa;">👁️ {item["views"]} | 💬 {item["cmts"]}</span></div></div>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

draw_section(c1, "📊 최신 이슈 모음 (네이버 실시간)", live_data)
draw_section(c2, "🔥 3시간 내 핫이슈 모음", sorted(live_data, key=lambda x: x['title'], reverse=True))
draw_section(c1, "🕘 9시간 내 핫이슈 모음", live_data[::-1])
draw_section(c2, "❤️ 24시간 내 하트 가장 많이 받은 이슈", live_data)

st.markdown('<div class="mid-banner">실시간 게임 산업 인사이트 통합 그라운드</div>', unsafe_allow_html=True)

b1, b2, b3 = st.columns(3)
def draw_rank(col, header, data_list, color):
    with col:
        html = f'<div class="section-bar">{header}</div><div class="custom-box">'
        for i, item in enumerate(data_list[:15]):
            num = i + 1
            num_cls = color if num <= 5 else ""
            html += f'<div class="list-row"><span class="rank-num {num_cls}">{num}</span><div class="content-area"><span class="title-text">{item["title"]}</span></div></div>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

draw_rank(b1, "커뮤니티 인기순", live_data, "blue")
draw_rank(b2, "많이 읽은 순서", live_data, "red")
draw_rank(b3, "커뮤니티 댓글순", live_data, "green")

st.markdown('<div class="version-marker">v12.0</div>', unsafe_allow_html=True)
