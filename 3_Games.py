import streamlit as st
from utils import get_live_games, get_past_games
from datetime import date

st.set_page_config(
    page_title="NBA Games",
    page_icon="🏀",
    layout="wide",
    menu_items={
        'About': 'https://github.com/slevin48/NBA'
    }
)

# Define the function to get the game for the selected date
def get_game_for_date(selected_date):
    if selected_date == date.today():
        return get_live_games()  
    else:
        return get_past_games(selected_date)

def display_fallback_content():
    st.write("We're currently unable to fetch game data. Here's some general NBA information:")
    st.write("- The NBA was founded on June 6, 1946.")
    st.write("- There are 30 teams in the NBA, divided into two conferences.")
    st.write("- The NBA season typically runs from October to April, followed by playoffs.")
    st.write("- The Boston Celtics have won the most NBA championships (17).")


# Main content
st.title("NBA Games 🏀")

# Add calendar to sidebar
st.sidebar.subheader("Select Date")
selected_date = st.sidebar.date_input("Choose a date", 
                                       value=date.today(),
                                       min_value=date(2024, 10, 1),
                                       max_value=date.today())

st.subheader(f"Games for {selected_date.strftime('%B %d, %Y')}")
games = get_game_for_date(selected_date)
# st.write(games)

if not games.empty:  # Correct way to check if DataFrame is not empty
    for _, game in games.iterrows():  # Use iterrows() to iterate through DataFrame rows
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.image(f"https://cdn.nba.com/logos/nba/{game['homeTeamId']}/global/L/logo.svg", width=100)
            st.write(f"[{game['homeTeamName']}](/Teams?team_id={game['homeTeamId']})")
            st.write(f"Score: {game['homeTeamScore']}")
        
        with col2:
            st.markdown("# VS")
        
        with col3:
            st.image(f"https://cdn.nba.com/logos/nba/{game['awayTeamId']}/global/L/logo.svg", width=100)
            st.write(f"[{game['awayTeamName']}](/Teams?team_id={game['awayTeamId']})")
            st.write(f"Score: {game['awayTeamScore']}")
        
        game_url = f"https://www.nba.com/game/{game['gameId']}"
        game_status = game['gameStatusText']
        st.write(f"Status: {game_status}",f" - [View game details on NBA.com]({game_url})")
        
        st.write("---")  # Add a separator between games
else:
    st.error("No games available for the selected date.")
    display_fallback_content()
