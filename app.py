import streamlit as st
import pandas as pd
import time

# 1. 페이지 설정 (레이아웃을 wide로 하되 CSS로 폭을 제한함)
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

# 2. PC환경 중앙 정렬 및 가독성 커스텀 CSS
st.markdown("""
    <style>
    /* 전체 배경색 */
    .stApp { background-color: #f2f2f2; }

    /* 메인 콘텐츠 폭 제한 및 중앙 정렬 (AAGAG 스타일) */
    @media (min-width: 1000px) {
        .block-container {
            max-width: 1100px !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            margin: auto;
        }
    }

    /* 최상단 타이틀 바 */
    .aagag-header {
        background-color: #3e4156;
        padding: 10px 20px;
        color: white;
        display: flex;
        align-items: center;
        margin-bottom: 20px;
        border-radius: 4px;
    }
    .aagag-header h1 { font-size: 20px; margin: 0; font-weight: 800; color: #fff; }

    /* 섹션 타이틀 바 */
    .section-bar {
        background-color: #55587c;
        color: white;
        padding: 5px 12px;
        font-size: 13px;
        font-weight: bold;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .section-bar span.more { font-weight: normal; font-size: 11px; color: #ddd; cursor: pointer; }

    /* 리스트 아이템 디자인 (밀도 높게) */
    .list-container {
        background-color: white;
        border: 1px solid #ddd;
        border-top: none;
        margin-bottom: 15px;
    }
    .list-item {
        display: flex;
        padding: 5px 10px;
        border-bottom: 1px solid #eee;
        font-size: 12px;
        align-items: center;
        transition: background 0.2s;
    }
    .list-item:hover { background-color: #f9f9f9; }
    .thumbnail {
        width: 36px; height: 36px; background-color: #eee;
        margin-right: 10px; border-radius: 2px; flex-shrink: 0;
    }
    .content-area { flex-grow: 1; overflow: hidden; }
    .title-text { 
        color: #333; font-weight: bold; font-size: 12px;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; 
    }
    .meta-text { font-size: 10px; color: #999; margin-top: 2px; }

    /* 하단 랭킹 숫자 */
    .rank-num { font-weight: bold; width: 20px; margin-right: 10px; font-size: 13px; color: #888; text-align: center; }
    .rank-num.blue { color: #3498db; }
    .rank-num.red { color: #e74c3c; }
    .rank-num.green { color: #27ae60; }

    /* 푸터 스타일 */
    .footer-msg {
        text-align: center; color: #ff8a8a; font-size: 12px; font-weight: bold;
        padding: 10px; background: #55587c; border-radius: 4px; margin: 20px 0;
    }
    </style>
""", unsafe_allow_html=True)

# 3. 데이터 로직 (예시 데이터)
def get_mock_data():
    items = []
    for i in range(40):
        items.append({
            "title": f"[{['분석','정보','공략','뉴스'][i%4]}] 게임 사업부 핫트래킹 리포트 #{i+1} - 상세 정보",
            "comm": ["인벤", "디시", "라운지", "루리웹"][i%4],
            "views": 1500 + (i * 320),
            "cmts": 12 + (i * 4),
            "time": i * 12, # 분 전
            "likes": 5 + (i * 2)
        })
    return pd.DataFrame(items)

df = get_mock_data()

# --- 화면 렌더링 시작 ---

# 상단 헤더
st.markdown('<div class="aagag-header"><h1>AAGIG: Game Insight Ground</h1></div>', unsafe_allow_html=True)

# 상단 4분할 격자 (PC 중앙 배치용)
c1, c2 = st.columns(2)

def draw_section(header, data):
    st.markdown(f'<div class="section-bar"><span>{header}</span><span class="more">더 보기</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="list-container">', unsafe_allow_html=True)
    for _, r in data.head(8).iterrows():
        st.markdown(f"""
            <div class="list-item">
                <div class="thumbnail"><img src="https://via.placeholder.com/36?text=G" style="width:100%;"></div>
                <div class="content-area">
                    <div class="title-text">{r['title']}</div>
                    <div class="meta-text">0.1 MB | 👁️ {r['views']} | 💬 {r['cmts']} | {r['time']}분 전</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c1:
    draw_section("최신 이슈 모음", df.sort_values('time'))
    draw_section("9 시간 내 핫이슈 모음", df[df['time'] <= 540].sort_values('views', ascending=False))

with c2:
    draw_section("3 시간 내 핫이슈 모음", df[df['time'] <= 180].sort_values('views', ascending=False))
    draw_section("24 시간 내 하트 많이 받은 이슈", df.sort_values('likes', ascending=False))

# 중간 안내 메시지
st.markdown('<div class="footer-msg">실시간 게임 이슈 Ground - AAGIG 배포 버전</div>', unsafe_allow_html=True)

# 하단 3분할 랭킹
b1, b2, b3 = st.columns(3)

def draw_rank(header, data, score_col, color_class):
    st.markdown(f'<div class="section-bar"><span>{header}</span><span class="more">더 보기</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="list-container">', unsafe_allow_html=True)
    for i, r in enumerate(data.head(15).iterrows()):
        num = i + 1
        st.markdown(f"""
            <div class="list-item">
                <div class="rank-num {color_class if num <= 5 else ''}">{num}</div>
                <div class="content-area">
                    <div class="title-text">{r[1]['title']}</div>
                </div>
                <div style="font-size:11px; color:#999; width:40px; text-align:right;">{r[1][score_col]}</div>
            </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with b1: draw_rank("커뮤니티 인기 (3시간)", df.sort_values('views', ascending=False), 'views', 'blue')
with b2: draw_rank("많이 읽은 순서 (3시간)", df.sort_values('likes', ascending=False), 'likes', 'red')
with b3: draw_rank("댓글 순위 (3시간)", df.sort_values('cmts', ascending=False), 'cmts', 'green')

# 노션 복사 버튼 (사이드바에 깔끔하게 배치)
with st.sidebar:
    st.title("AAGIG Control")
    if st.button("📝 Copy for Notion"):
        st.code(df.head(10)[['title', 'comm']].to_markdown())
        st.success("클립보드에 복사하세요!")
