import streamlit as st
import pandas as pd
import requests
import re
import json
import os
import urllib.parse
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET
import difflib
import html
from bs4 import BeautifulSoup

# cloudscraper 추가 (Cloudflare 및 TIG 403 우회 강화)
try:
    import cloudscraper
    # 봇이 아닌 진짜 윈도우 크롬 브라우저인 것처럼 정밀 위장
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )
    HAS_CLOUDSCRAPER = True
except ImportError:
    HAS_CLOUDSCRAPER = False
    scraper = None

# 번역 라이브러리
try:
    from deep_translator import GoogleTranslator
    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False

# 1. 페이지 설정
st.set_page_config(page_title="AAGIG - Game Insight Ground", layout="wide")

# 2. 스타일 시트
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
    .title-text:hover { color: #3b82f6 !important; text-decoration: underline !important; }
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
    .error-box { background-color: #fee; border: 1px solid #fcc; padding: 8px; margin: 8px 0; border-radius: 4px; font-size: 11px; color: #c33; }
</style>
""", unsafe_allow_html=True)

# UI 선출력
try: 
    st.image("division8_centered_1800x300.png", use_column_width=True)
except: 
    pass
st.markdown('<div class="sub-logo-header">AAGIG: 8실 Game Insight Ground</div>', unsafe_allow_html=True)

# 3. 보조 로직
def translate_title(text):
    if not re.search('[a-zA-Z]', text) or re.search('[가-힣]', text): 
        return text
    if HAS_TRANSLATOR:
        try: 
            return GoogleTranslator(source='auto', target='ko').translate(text)
        except Exception as e:
            pass
    return text

def is_similar_title(new_title, existing_titles, threshold=0.65):
    recent_titles = existing_titles[-50:] if len(existing_titles) > 50 else existing_titles
    for ext_title in recent_titles:
        if difflib.SequenceMatcher(None, new_title, ext_title).ratio() > threshold: 
            return True
    return False

def get_relative_time(timestamp):
    diff = datetime.now().timestamp() - timestamp
    if diff < 0: return "방금 전"
    if diff < 86400:
        if diff >= 3600: return f"{int(diff // 3600)}시간 전"
        if diff >= 60: return f"{int(diff // 60)}분 전"
        return "방금 전"
    return f"{int(diff // 86400)}일 전"

def extract_time_from_text(text):
    now = datetime.now()
    if re.search(r'방금\s*전', text): return now.timestamp()
    
    match = re.search(r'(\d+)\s*(시간|분|일)\s*전', text)
    if match:
        val, unit = int(match.group(1)), match.group(2)
        if unit == '시간': return (now - timedelta(hours=val)).timestamp()
        if unit == '분': return (now - timedelta(minutes=val)).timestamp()
        if unit == '일': return (now - timedelta(days=val)).timestamp()
    
    match = re.search(r'(202[0-9])[./-](0[1-9]|1[0-2]|[1-9])[./-](0[1-9]|[12][0-9]|3[01]|[1-9])\s+([01]?[0-9]|2[0-3]):([0-5][0-9])', text)
    if match: return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4)), int(match.group(5))).timestamp()
    
    match = re.search(r'(202[0-9])[./-](0[1-9]|1[0-2]|[1-9])[./-](0[1-9]|[12][0-9]|3[01]|[1-9])', text)
    if match: return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3))).timestamp()
    
    match = re.search(r'(0[1-9]|1[0-2]|[1-9])[./-](0[1-9]|[12][0-9]|3[01]|[1-9])\s+([01]?[0-9]|2[0-3]):([0-5][0-9])', text)
    if match: return datetime(now.year, int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))).timestamp()
    
    match = re.search(r'(0[1-9]|1[0-2]|[1-9])[./-](0[1-9]|[12][0-9]|3[01]|[1-9])', text)
    if match: return datetime(now.year, int(match.group(1)), int(match.group(2))).timestamp()
    
    match = re.search(r'([01]?[0-9]|2[0-3]):([0-5][0-9])', text)
    if match: return now.replace(hour=int(match.group(1)), minute=int(match.group(2)), second=0).timestamp()
    
    return None

def get_thumbnail(container, source, url):
    thumb = ""
    imgs = container.find_all('img')
    spam_keywords = ['icon', 'logo', 'blank', 'gif', 'profile', 'avatar', 'tracker', 'svg', 'button']
    
    for img in imgs:
        for attr in ['data-lazysrc', 'data-original', 'data-src', 'data-lazy-src', 'src']:
            val = img.get(attr)
            if not val: continue
            val_lower = val.lower()
            if val_lower.startswith('data:image'): continue
            if any(spam in val_lower for spam in spam_keywords): continue
            
            thumb = val
            break
        if thumb: break

    if thumb:
        if thumb.startswith('//'):
            thumb = f"https:{thumb}"
        elif not thumb.startswith('http'):
            thumb = f"{urllib.parse.urlparse(url).scheme}://{urllib.parse.urlparse(url).netloc}{thumb}"
            
    if not thumb: 
        thumb = f"https://www.google.com/s2/favicons?domain={source}.com&sz=128"
    return thumb

# 4. DB 관리 (v62 로 업데이트하여 오염된 링크/제목 캐시 완전 파기)
DB_FILE = "aagig_db_v62.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
    return []

def save_db(data):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)
    except: pass

# 5. 크롤링 엔진
@st.cache_data(ttl=60)
def update_articles():
    current_db = load_db()
    existing_links = {item['link'] for item in current_db}
    existing_titles = [item['title'] for item in current_db]
    new_articles = []
    errors = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    # --- [1] RSS ---
    rss_feeds = [
        ("https://www.gamespot.com/feeds/news/", "GameSpot", "tag-global", "global", 20),
        ("https://news.google.com/rss/search?q=서정근+MTN&hl=ko&gl=KR&ceid=KR:ko", "MTN", "tag-mtn", "mtn_only", 15)
    ]
    
    for rss_url, source_name, tag, group, cap in rss_feeds:
        try:
            r = requests.get(rss_url, headers=headers, timeout=10)
            r.raise_for_status()
            root = ET.fromstring(r.text)
            feed_temp = []
            
            for item in root.findall('.//item'):
                try:
                    title = item.find('title').text.strip()
                    link = item.find('link').text.strip()
                    if link in existing_links: continue
                    final_title = translate_title(title) if group == "global" else title
                    if is_similar_title(final_title, existing_titles): continue
                    
                    thumb = ""
                    media = item.find('{http://search.yahoo.com/mrss/}content')
                    if media is not None: thumb = media.get('url')
                    if not thumb:
                        enc = item.find('enclosure')
                        if enc is not None: thumb = enc.get('url')
                    if not thumb:
                        desc = item.find('description')
                        if desc is not None:
                            match = re.search(r'src="([^"]+)"', desc.text)
                            if match: thumb = match.group(1)
                    if not thumb: thumb = f"https://www.google.com/s2/favicons?domain={source_name}.com&sz=128"

                    pub_node = item.find('pubDate')
                    timestamp = parsedate_to_datetime(pub_node.text).timestamp() if pub_node is not None else datetime.now().timestamp()
                    
                    feed_temp.append({"title": final_title, "link": link, "source": source_name, "tag": tag, "group": group, "thumb": thumb, "timestamp": timestamp})
                except: pass
            
            feed_temp.sort(key=lambda x: x['timestamp'], reverse=True)
            for art in feed_temp[:cap]:
                new_articles.append(art)
                existing_links.add(art['link'])
                existing_titles.append(art['title'])
                
        except Exception as e:
            errors.append(f"RSS 실패 ({source_name}): {e}")

    # --- [2] HTML 스크래핑 ---
    html_targets = [
        ("https://www.thisisgame.com/articles?newsId=400003&categoryId=0", "TIG", "tag-kr"),
        ("https://www.thisisgame.com/articles?newsId=400004&categoryId=0", "TIG", "tag-kr"),
        ("https://www.thisisgame.com/articles?newsId=400005&categoryId=0", "TIG", "tag-kr"),
        ("https://www.thisisgame.com/articles?newsId=400011&categoryId=0", "TIG", "tag-kr"),
        ("https://www.thisisgame.com/articles?newsId=400012&categoryId=0", "TIG", "tag-kr"),
        ("https://www.inven.co.kr/webzine/news/?sclass=12&platform=gamereview", "인벤", "tag-inven"),
        ("https://www.inven.co.kr/webzine/news/?sclass=24", "인벤", "tag-inven"),
        ("https://www.inven.co.kr/webzine/news/?sclass=25", "인벤", "tag-inven"),
        ("https://www.gamemeca.com/review.php", "게임메카", "tag-kr"),
        ("https://www.gamemeca.com/feature.php", "게임메카", "tag-kr"),
        ("https://zdnet.co.kr/news/?lstcode=0060", "ZDNet", "tag-kr"),
        ("https://dealsite.co.kr/search/?LIKE=%EB%84%A5%EC%8A%A8&SEARCHFIELD=TITLE_CONTENT&sp=m1&ALSOLIKE=&NOTLIKE=&searchStartDt=&searchEndDt=", "딜사이트", "tag-biz"),
        ("https://bbs.ruliweb.com/news/board/11?cate=1035,1037,1039&view=gallery", "루리웹", "tag-kr"),
        ("https://www.fetv.co.kr/news/section_list_all.html?sec_no=59", "FETV", "tag-biz")
    ]
    
    # 쿠폰, 무료, 광고 등 스팸 키워드 강화
    blacklist = ['[질문]', '[잡담]', '[단편]', '[연재]', '올림픽', '아시안게임', '만화', '서적', '결혼', '부고', '게시판', '공지사항', '이용안내', '증권', '펀드', '자산운용', '투자증권', 'ISA', '코스닥', '주식', '청약', '금리', '환율', '특징주', '쿠폰', '무료', '광고', '협찬', '할인']
    game_whitelist = ['게임', '넥슨', '넷마블', '엔씨', '크래프톤', '카카오게임즈', '스마일게이트', '펄어비스', '위메이드', '컴투스', '스팀', '콘솔', 'PC', 'e스포츠', '게이머', '신작', '플레이', 'RPG', 'MMO']

    for url, source, tag in html_targets:
        try:
            if HAS_CLOUDSCRAPER:
                r = scraper.get(url, timeout=10)
            else:
                r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            
            soup = BeautifulSoup(r.text, 'html.parser')
            count = 0
            
            for container in soup.find_all(['li', 'tr', 'div']):
                container_classes = " ".join(container.get('class', [])).lower()
                if any(skip_word in container_classes for skip_word in ['notice', 'ad', 'headline', '공지']): 
                    continue
                if container.find_parent(class_=re.compile(r'(side|best|rank|hit|wing|right)', re.I)) or container.find_parent(id=re.compile(r'(side|best|rank|hit|wing|right)', re.I)): 
                    continue
                
                text_len = len(container.get_text(strip=True))
                if text_len < 10: 
                    continue
                
                title_a = None
                
                # [핵심 수술] 예비 로직 전면 폐기! 오직 정확한 기사 제목 링크 태그만 스나이핑
                if source == "딜사이트":
                    title_a = container.select_one('.sn_title a, .title a, h3 a, .sn_tit a, strong.tit a')
                elif source == "게임메카":
                    title_a = container.select_one('.list_tit a, .tit a, strong a')
                elif source == "루리웹":
                    title_a = container.select_one('.title a, a.deco, .subject a')
                elif source == "인벤":
                    title_a = container.select_one('.title a, .name a, .subject a')
                elif source == "TIG":
                    title_a = container.select_one('.list-title a, .tit a, .subject a')
                elif source == "FETV":
                    title_a = container.select_one('.tit a, .title a')
                else: # ZDNet 등 나머지
                    title_a = container.select_one('a')
                
                # 정확한 태그를 못 찾았으면 미련 없이 버림 (메뉴바/위젯 오작동 차단)
                if not title_a:
                    continue
                
                title = title_a.get_text(strip=True)
                link = title_a['href']
                
                if not link.startswith('http'): 
                    link = f"{urllib.parse.urlparse(url).scheme}://{urllib.parse.urlparse(url).netloc}{link}"
                
                if any(spam in link for spam in ['smartstore', 'market.inven', 'shopping']): continue
                if link in existing_links or "javascript:" in link: continue
                if any(b in title for b in blacklist): continue
                if source in ["FETV", "딜사이트"] and not any(w in title for w in game_whitelist): continue
                if is_similar_title(title, existing_titles): continue

                thumb = get_thumbnail(container, source, url)
                
                container_text = container.get_text(separator=' ')
                ts = extract_time_from_text(container_text)
                if not ts: 
                    ts = datetime.now().timestamp() - 600 - (count * 60)
                
                new_articles.append({
                    "title": title, 
                    "link": link, 
                    "source": source, 
                    "tag": tag, 
                    "group": "domestic", 
                    "thumb": thumb, 
                    "timestamp": ts
                })
                existing_links.add(link)
                existing_titles.append(title)
                
                count += 1
                if count >= 5: 
                    break
                    
        except Exception as e:
            errors.append(f"HTML 수집 실패 ({source}): {e}")

    if errors:
        with st.expander(f"⚠️ 수집 중 {len(errors)}개 오류 발생 (클릭해서 확인)", expanded=False):
            for err in errors:
                st.markdown(f'<div class="error-box">{err}</div>', unsafe_allow_html=True)

    final_db = sorted((current_db + new_articles), key=lambda x: x['timestamp'], reverse=True)
    save_db(final_db[:300])
    return final_db

with st.spinner('14개 소스에서 기사 수집 중...'):
    live_data = update_articles()

dom = [d for d in live_data if d['group'] == "domestic"]
glo = [d for d in live_data if d['group'] == "global"]
mtn = [d for d in live_data if d['group'] == "mtn_only"]

def draw_box(col, header, data_list):
    with col:
        st.markdown(f'<div class="section-bar"><span>{header}</span><a href="#" class="more-btn">더보기 ➔</a></div>', unsafe_allow_html=True)
        html_str = '<div class="custom-box">'
        for r in data_list[:8]:
            fallback = f"https://www.google.com/s2/favicons?domain={r['source']}.com&sz=128"
            thumb = r['thumb'] if r['thumb'] else fallback
            region = "KR" if r['group'] != "global" else "GL"
            reg_cls = "tag-kr" if r['group'] != "global" else "tag-gl"
            safe_title = html.escape(r['title'])
            
            html_str += f"""
            <div class="list-row">
                <div class="thumb-box"><img src="{thumb}" onerror="this.src='{fallback}'"></div>
                <div class="content-area">
                    <a href="{r['link']}" target="_blank" class="title-text">{safe_title}</a>
                    <div class="meta-area">
                        <span class="source-tag {r['tag']}">{r['source']}</span>
                        <span class="source-tag {reg_cls}">{region}</span>
                        <span>🕒 {get_relative_time(r['timestamp'])}</span>
                    </div>
                </div>
            </div>"""
        html_str += '</div>'
        st.markdown(html_str, unsafe_allow_html=True)

r1_c1, r1_c2 = st.columns(2)
draw_box(r1_c1, "국내 주요 매체/웹진", dom)
draw_box(r1_c2, "글로벌 트렌드", glo)

r2_c1, r2_c2 = st.columns(2)
draw_box(r2_c1, "국내 핫 이슈", dom[8:16])
draw_box(r2_c2, "글로벌 핫 이슈", glo[8:16])

r3_c1, r3_c2 = st.columns(2)
draw_box(r3_c1, "전체 최신 기사", (dom+glo)[16:32])
draw_box(r3_c2, "MTN 서정근 인사이트", mtn)

st.markdown('<div class="mid-banner">실시간 게임 산업 인사이트 통합 그라운드</div>', unsafe_allow_html=True)
st.markdown('<div class="version-marker">v122.0 (Strict Title/Link Lock-on & TIG Cloudflare Bypass)</div>', unsafe_allow_html=True)
