import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

# 1. 페이지 레이아웃 및 디자인 (기존 유지)
st.set_page_config(page_title="AAGAG 이슈 트래커 Ver 2.1", layout="wide")
st.markdown("""
    <style>
    .aagag-list { font-family: 'Malgun Gothic', sans-serif; font-size: 13px; line-height: 1.6; }
    .aagag-item { border-bottom: 1px solid #eee; padding: 4px 0; display: flex; justify-content: space-between; align-items: center; }
    .rank { font-weight: bold; color: #888; width: 25px; display: inline-block; text-align: center; }
    .community-tag { font-size: 11px; background: #f0f0f0; color: #666; padding: 1px 4px; border-radius: 2px; margin-right: 5px; }
    .title-text { color: #333; text-decoration: none; overflow: hidden; text-overflow: ellipsis; max-width: 200px; display: inline-block; vertical-align: middle;}
    .header-bar { background: #55587c; color: white; padding: 8px 12px; font-weight: bold; font-size: 14px; margin-bottom: 5px; }
    .metric-box { border: 1px solid #ddd; padding: 10px; border-top: 3px solid #55587c; text-align: center; background: #fff; }
    </style>
""", unsafe_allow_html=True)

# 2. 보안 돌파용 강화된 크롤링 함수
def get_data_safe():
    # 인벤 '전체글보기' 주소로 변경하여 데이터 확보 확률 업
    url = "https://www.inven.co.kr/board/powerbbs.php?come_idx=2097&p=1"
    
    # 실제 크롬 브라우저처럼 보이기 위한 정밀 세팅
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    try:
        # verify=False를 추가하여 SSL 인증서 에러(회사 보안망 이슈) 방지
        res = requests.get(url, headers=headers, timeout=10, verify=True)
        res.raise_for_status() # 에러 발생 시 예외 처리
        res.encoding = 'utf-8' # 한글 깨짐 방지
        
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 인벤 게시판의 새로운 구조까지 대응 (두 가지 선택자 시도)
        rows = soup.select('tr.ls') or soup.select('.sjnamelist tr')
        
        results = []
        for row in rows:
            # 제목 찾기 (클래스명이 다를 경우 대비)
            t_el = row.select_one('.sj__title') or row.select_one('.tit')
            v_el = row.select_one('.sj__view') or row.select_one('.view')
            c_el = row.select_one('.sj__cmt') or row.select_one('.cmt')
            
            if not t_el or "공지" in row.get_text(): continue
            
            title = t_el.get_text(strip=True)
            # 조회수 숫자 파싱
            try:
                raw_v = v_el.get_text(strip=True).replace(',', '') if v_el else "0"
                views = int(''.join(filter(str.isdigit, raw_v)) or 0)
            except: views = 0
            
            # 댓글수 숫자 파싱
            try:
                raw_c = c_el.get_text(strip=True).replace('[','').replace(']','') if c_el else "0"
                cmts = int(''.join(filter(str.isdigit, raw_c)) or 0)
            except: cmts = 0
            
            # 간단 감성 로직
            sentiment = "부정" if any(w in title for w in ["망", "핵", "버그", "실화", "삭제", "점검", "정지"]) else "긍정"
            trend = (views * 0.02) + (cmts * 5)
            risk = trend * 1.5 if sentiment == "부정" else trend
            
            results.append({
                "title": title, "comm": "인벤", "views": views, 
                "cmts": cmts, "sent": sentiment, "trend": round(trend), "risk": round(risk)
            })
            
        return pd.DataFrame(results)
    except Exception as e:
        # 에러 발생 시 화면에 구체적인 이유 출력 (디버깅용)
        st.error(f"상세 에러 내용: {e}")
        return pd.DataFrame()

# --- 메인 화면 ---
st.title("📂 AAGAG Game Insight Dashboard")

if st.sidebar.button("🔄 데이터 강제 새로고침"):
    st.cache_data.clear()

df = get_data_safe()

if not df.empty:
    # (상단 지표 및 리스트업 로직은 이전과 동일)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("수집 게시물", f"{len(df)}건")
    m2.metric("부정적 이슈", f"{len(df[df['sent']=='부정'])}건", delta_color="inverse")
    m3.metric("평균 화제성", int(df['trend'].mean()))
    m4.metric("최고 위험도", df['risk'].max())

    st.write("")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="header-bar">🚨 긴급 대응 요망 (위험도순)</div>', unsafe_allow_html=True)
        for i, r in enumerate(df.sort_values('risk', ascending=False).head(15).to_dict('records')):
            st.markdown(f'<div class="aagag-item"><span><span class="rank">{i+1}</span><span class="community-tag">{r["comm"]}</span><span class="title-text">{r["title"]}</span></span><span style="color:red; font-weight:bold; font-size:11px;">{r["risk"]}</span></div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="header-bar">🔥 실시간 핫 이슈 (화제성순)</div>', unsafe_allow_html=True)
        for i, r in enumerate(df.sort_values('trend', ascending=False).head(15).to_dict('records')):
            st.markdown(f'<div class="aagag-item"><span><span class="rank">{i+1}</span><span class="community-tag">{r["comm"]}</span><span class="title-text">{r["title"]}</span></span><span style="color:blue; font-weight:bold; font-size:11px;">{r["trend"]}</span></div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="header-bar">💬 화력 집중 (댓글순)</div>', unsafe_allow_html=True)
        for i, r in enumerate(df.sort_values('cmts', ascending=False).head(15).to_dict('records')):
            st.markdown(f'<div class="aagag-item"><span><span class="rank">{i+1}</span><span class="community-tag">{r["comm"]}</span><span class="title-text">{r["title"]}</span></span><span style="font-size:11px; color:#666;">{r["cmts"]} cmt</span></div>', unsafe_allow_html=True)
else:
    st.info("데이터를 분석 중이거나 사이트 접근을 시도 중입니다. 잠시만 기다려주세요.")