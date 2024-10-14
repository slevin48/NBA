import streamlit as st
from nba_api.stats.static import players
from utils import fetch_data
from nba_api.stats.endpoints import commonplayerinfo, playergamelog

st.set_page_config(
    page_title="NBA Players", 
    layout="wide",
    page_icon="🏀")

def show_players():
    st.title("NBA Players")
    all_players = players.get_active_players()
    player_names = [f"{player['first_name']} {player['last_name']}" for player in all_players]
    selected_player = st.selectbox("Select a player", player_names)

    if selected_player:
        player = next(player for player in all_players if f"{player['first_name']} {player['last_name']}" == selected_player)
        player_id = player['id']
        stats_nba_url = f"https://www.nba.com/stats/player/{player_id}"
        st.sidebar.markdown(f"## [{selected_player}]({stats_nba_url})")
        
        # Get player image
        image_url = f"https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/{player_id}.png"
        # Display player image in sidebar
        st.sidebar.image(image_url, caption=selected_player)
  
        player_info = fetch_data(commonplayerinfo.CommonPlayerInfo, player_id=player_id)
        
        if player_info is not None:
            with st.sidebar.expander("Player Details"):
                team_id = player_info.TEAM_ID.iloc[0]
                st.markdown(f"Team: [{player_info.TEAM_NAME.iloc[0]}](Teams?team_id={team_id})", unsafe_allow_html=True)
                st.write(f"Position: {player_info.POSITION.iloc[0]}")
                st.write(f"Height: {player_info.HEIGHT.iloc[0]}")
                st.write(f"Weight: {player_info.WEIGHT.iloc[0]}")
                st.write(f"Country: {player_info.COUNTRY.iloc[0]}")

        # Fetch last game performance
        game_log = fetch_data(playergamelog.PlayerGameLog, player_id=player_id, season='2023-24')
        
        if game_log is not None and not game_log.empty:
            last_game = game_log.iloc[0]
            
            st.subheader("Last Game Performance")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Points", last_game['PTS'])
                st.metric("Rebounds", last_game['REB'])
                st.metric("Assists", last_game['AST'])
            
            with col2:
                st.metric("Steals", last_game['STL'])
                st.metric("Blocks", last_game['BLK'])
                st.metric("Minutes", last_game['MIN'])
            
            st.write(f"Game Date: {last_game['GAME_DATE']}")
            st.write(f"Matchup: {last_game['MATCHUP']}")
        else:
            st.write("No recent game data available for this player.")

# if __name__ == "__main__":
show_players()
