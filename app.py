import streamlit as st
import random
import time
from nba_api.stats.endpoints import commonteamroster, playercareerstats
from nba_api.stats.static import teams

# --- 팀 컬러 및 로고 함수 ---
TEAM_COLORS = {
    "Atlanta Hawks": {"main": "#E03A3E", "dark": "#C1D32F"}, "Boston Celtics": {"main": "#007A33", "dark": "#004A1D"},
    "Brooklyn Nets": {"main": "#000000", "dark": "#FFFFFF"}, "Charlotte Hornets": {"main": "#1D1160", "dark": "#00788C"},
    "Chicago Bulls": {"main": "#CE1141", "dark": "#8C0D2C"}, "Cleveland Cavaliers": {"main": "#860038", "dark": "#FDBB30"},
    "Dallas Mavericks": {"main": "#00538C", "dark": "#002B5E"}, "Denver Nuggets": {"main": "#0E2240", "dark": "#FEC524"},
    "Detroit Pistons": {"main": "#C8102E", "dark": "#1D428A"}, "Golden State Warriors": {"main": "#1D428A", "dark": "#FFC72C"},
    "Houston Rockets": {"main": "#CE1141", "dark": "#990024"}, "Indiana Pacers": {"main": "#002D62", "dark": "#FDBB30"},
    "Los Angeles Clippers": {"main": "#C8102E", "dark": "#1D428A"}, "Los Angeles Lakers": {"main": "#552583", "dark": "#FDB927"},
    "Memphis Grizzlies": {"main": "#5D76A9", "dark": "#12173F"}, "Miami Heat": {"main": "#98002E", "dark": "#F9A01B"},
    "Milwaukee Bucks": {"main": "#00471B", "dark": "#EEE1C6"}, "Minnesota Timberwolves": {"main": "#0C2340", "dark": "#236192"},
    "New Orleans Pelicans": {"main": "#0C2340", "dark": "#C8102E"}, "New York Knicks": {"main": "#006BB6", "dark": "#F58426"},
    "Oklahoma City Thunder": {"main": "#007AC1", "dark": "#EF3B24"}, "Orlando Magic": {"main": "#0077C0", "dark": "#000000"},
    "Philadelphia 76ers": {"main": "#006BB6", "dark": "#ED174C"}, "Phoenix Suns": {"main": "#1D1160", "dark": "#E56020"},
    "Portland Trail Blazers": {"main": "#E03A3E", "dark": "#000000"}, "Sacramento Kings": {"main": "#5A2D81", "dark": "#63727A"},
    "San Antonio Spurs": {"main": "#C4CED4", "dark": "#000000"}, "Toronto Raptors": {"main": "#CE1141", "dark": "#000000"},
    "Utah Jazz": {"main": "#002B5C", "dark": "#F9A01B"}, "Washington Wizards": {"main": "#002B5C", "dark": "#E31837"},
    "default": {"main": "#1D428A", "dark": "#002B5C"}
}

def get_team_colors(team_name): return TEAM_COLORS.get(team_name, TEAM_COLORS["default"])
def get_team_logo_url(team_name):
    team_info = [t for t in teams.get_teams() if t['full_name'] == team_name][0]
    return f"https://cdn.nba.com/logos/nba/{team_info['id']}/global/L/logo.svg"

# --- 페이지 설정 ---
st.set_page_config(page_title="82-0 Franchise", page_icon="KakaoTalk_20260531_182647350.jpg", layout="wide")
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif !important; }
    
    /* --- 추가된 부분: Streamlit 기본 UI 요소 완벽 숨기기 --- */
    header {visibility: hidden !important;} /* 우측 상단 햄버거 메뉴 및 헤더 바 숨김 */
    footer {visibility: hidden !important;} /* 하단 Made with Streamlit 숨김 */
    [data-testid="stToolbar"] {visibility: hidden !important;} /* 추가적인 툴바 요소 숨김 */
    
    .stApp { background-color: #f8f9fa; }
    .result-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; margin: 0 auto; }
    .pos-box { padding: 10px 20px; border-radius: 8px; margin-bottom: 8px; color: white; font-weight: bold; border-left: 8px solid; width: 100%; max-width: 350px; text-align: left; }
    .win-loss { font-size: 4rem; font-weight: 800; text-align: center; margin-top: 20px; }
    .info-box { background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 25px 35px; border-radius: 12px; display: inline-block; text-align: left; margin-top: 20px; color: #495057; font-size: 1.1rem; line-height: 1.8; }
    </style>
""", unsafe_allow_html=True)

# --- 최적화된 데이터 호출 함수 ---
@st.cache_data(ttl=86400)
def get_roster(team_name, season_full):
    try:
        team_id = [t['id'] for t in teams.get_teams() if t['full_name'] == team_name][0]
        roster_data = commonteamroster.CommonTeamRoster(team_id=team_id, season=season_full).get_data_frames()[0]
        return roster_data[['PLAYER', 'PLAYER_ID', 'POSITION']].to_dict('records')
    except: return []

@st.cache_data(ttl=86400)
def get_player_stats(pid, season_full):
    try:
        career = playercareerstats.PlayerCareerStats(player_id=pid).get_data_frames()[0]
        stats = career[career['SEASON_ID'] == season_full]
        if stats.empty: return None
        gp = stats['GP'].values[0]
        if gp == 0: return None
        
        s = {'PTS': stats['PTS'].values[0]/gp, 'REB': stats['REB'].values[0]/gp, 'AST': stats['AST'].values[0]/gp, 
             'STL': stats['STL'].values[0]/gp, 'BLK': stats['BLK'].values[0]/gp, '3PM': stats['FG3M'].values[0]/gp, 'TOV': stats['TOV'].values[0]/gp}
        return s
    except: return None

# --- 상태 초기화 ---
if 'team' not in st.session_state: st.session_state.team = None
if 'my_roster' not in st.session_state: st.session_state.my_roster = {}
if 'temp_season' not in st.session_state: st.session_state.temp_season = None
if 'roster_details' not in st.session_state: st.session_state.roster_details = {}
if 'selected_players' not in st.session_state: st.session_state.selected_players = []

# --- 메인 로직 ---
if not st.session_state.team:
    random_title_color = random.choice(list(TEAM_COLORS.values()))["main"]
    
    st.markdown(f"""
        <style>
        .start-card {{
            background-color: white; 
            padding: 50px 40px 110px 40px; 
            border-radius: 15px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
            text-align: center; 
        }}
        .stButton {{
            margin-top: -95px !important; 
            position: relative;
            z-index: 10;
        }}
        .stButton button p {{
            font-family: 'Pretendard', sans-serif !important;
            font-weight: 500 !important;
            font-size: 1.1rem !important;
        }}
        </style>
        
        <div class='start-card'>
            <div style='font-size: clamp(2.5rem, 8vw, 4.5rem); font-weight:800; color:{random_title_color}; margin-bottom: 5px; letter-spacing: -1px; line-height: 1.2;'>Can you go <span style="white-space: nowrap;">82-0?</span></div>
            <div style='font-size: clamp(1.2rem, 4vw, 2rem); color:#000000; font-weight:500; margin-bottom: 15px;'>With your own franchise</div>
            <div class='info-box'>
                <div><strong>1. 시즌 :</strong> 플레이-바이-플레이 도입 이래 97-98 ~ 25-26</div>
                <div><strong>2. 팀 빌드 :</strong> 가드 2 - 포워드 2 - 센터 1</div>
                <div><strong>3. 조건 :</strong> 팀, 시즌 변경 불가</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        if st.button("Start", use_container_width=True):
            st.session_state.team = random.choice([t['full_name'] for t in teams.get_teams()])
            y = random.randint(1997, 2025)
            st.session_state.temp_season = f"{y}-{str(y+1)[2:]}"
            st.rerun()
else:
    colors = get_team_colors(st.session_state.team)
    
    # 로스터 완성 시 결과 화면
    if len(st.session_state.my_roster) >= 5:
        with st.spinner('Calculating...'): time.sleep(2)
        
        total_ovr = sum([s['PTS'] + (s['REB']*1.5) + (s['AST']*1.5) + (s['STL']+s['BLK'])*3 + (s['3PM']*3) - (s['TOV']*3) for s in st.session_state.roster_details.values()])
        wins = min(82, max(0, int((total_ovr - 70) / 1.75)))
        
        if wins == 82:
            title_text = "Congratulations!"
        elif 67 <= wins <= 81:
            title_text = "Dynasty"
        elif 57 <= wins <= 66:
            title_text = "Contender"
        elif 42 <= wins <= 56:
            title_text = "Playoff"
        elif 33 <= wins <= 41:
            title_text = "Play In"
        elif 21 <= wins <= 32:
            title_text = "Rebuilding"
        else:
            title_text = "Tanking"
            
        st.markdown(f"<h1 style='text-align:center; color:{colors['dark']}; font-weight:900; font-size: clamp(2.5rem, 8vw, 3.5rem); margin-bottom: 30px;'>{title_text}</h1>", unsafe_allow_html=True)
        
        result_html = "<div class='result-container'>"
        
        for pos in ["PG", "SG", "SF", "PF", "C"]:
            val = st.session_state.my_roster.get(pos, "")
            result_html += f"<div class='pos-box' style='background-color: {colors['main']}; border-left-color: {colors['dark']};'>{pos}: {val}</div>"
        
        result_html += f"<div class='win-loss' style='color:{colors['dark']};'>{wins} - {82-wins}</div>"
        result_html += "</div>"
        
        st.markdown(result_html, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Restart", use_container_width=True):
                st.session_state.team, st.session_state.my_roster, st.session_state.roster_details, st.session_state.temp_season, st.session_state.selected_players = None, {}, {}, None, []
                st.rerun()
            
    # 로스터 구성 중 화면
    else:
        col_left, col_right = st.columns([1.5, 1])
        
        with col_right:
            st.subheader("Roster")
            for pos in ["PG", "SG", "SF", "PF", "C"]:
                val = st.session_state.my_roster.get(pos, "")
                st.markdown(f"<div class='pos-box' style='background-color: {colors['main'] if val else '#D1D5DB'}; border-left-color: {colors['dark'] if val else '#9CA3AF'}; width: 100%;'>{pos}: {val}</div>", unsafe_allow_html=True)
                
        with col_left:
            st.markdown(f"<div style='display: flex; align-items: center; margin-bottom: 15px;'><img src='{get_team_logo_url(st.session_state.team)}' style='width: 45px; margin-right: 15px;'><h3 style='margin: 0;'>Team: <strong>{st.session_state.team}</strong></h3></div>", unsafe_allow_html=True)
            st.write(f"#### Season: {st.session_state.temp_season[2:]}")
            
            raw_roster = get_roster(st.session_state.team, st.session_state.temp_season)
            player_list = []
            for r in raw_roster:
                if r['PLAYER'] not in st.session_state.selected_players:
                    player_list.append({'label': f"{r['PLAYER']} ({r['POSITION']})", 'name': r['PLAYER'], 'id': r['PLAYER_ID'], 'pos': r['POSITION']})
            
            player_list.sort(key=lambda x: x['name'])
            
            if player_list:
                sel = st.selectbox("Choose a player:", [p['label'] for p in player_list])
                sp = next(p for p in player_list if p['label'] == sel)
                
                pos_list = [slot for slot in (["PG", "SG"] if "G" in sp['pos'] else []) + (["SF", "PF"] if "F" in sp['pos'] else []) + (["C"] if "C" in sp['pos'] else []) if slot not in st.session_state.my_roster]
                tp = st.selectbox("Select slot:", pos_list) if pos_list else None
                
                if st.button("Confirm"):
                    if not tp: 
                        st.error("이 선수를 넣을 수 있는 포지션 슬롯이 꽉 찼습니다!")
                    else:
                        with st.spinner(f"{sp['name']} 선수의 스탯을 불러오는 중..."):
                            stats = get_player_stats(sp['id'], st.session_state.temp_season)
                            
                            if stats:
                                st.session_state.my_roster[tp] = f"{st.session_state.temp_season[2:]} {sp['name']}"
                                st.session_state.selected_players.append(sp['name'])
                                st.session_state.roster_details[tp] = stats
                                
                                y = random.randint(1997, 2025)
                                st.session_state.temp_season = f"{y}-{str(y+1)[2:]}"
                                st.rerun()
                            else:
                                st.error("해당 시즌에 스탯 기록(출전)이 없는 선수입니다. 다른 선수를 선택해주세요.")
            else:
                st.warning("선택할 수 있는 선수가 없습니다. 시즌을 다시 굴립니다.")
                if st.button("Re-roll Season"):
                    y = random.randint(1997, 2025)
                    st.session_state.temp_season = f"{y}-{str(y+1)[2:]}"
                    st.rerun()