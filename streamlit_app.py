import streamlit as st
from nba_api.live.nba.endpoints import scoreboard
from datetime import datetime, date
from requests.exceptions import RequestException
import time

st.set_page_config(
    page_title="NBA Data App",
    page_icon="🏀",
    initial_sidebar_state="expanded"
)

st.sidebar.header("Home")

def get_game_for_date(selected_date, max_retries=3):
    for _ in range(max_retries):
        try:
            # Convert selected_date to the required format
            formatted_date = selected_date.strftime('%m/%d/%Y')
            score_board = scoreboard.ScoreBoard()
            games = score_board.games.get_dict()
            
            # Filter games for the selected date
            filtered_games = [game for game in games if game['gameTimeUTC'].startswith(selected_date.strftime('%Y-%m-%d'))]
            
            if filtered_games:
                return filtered_games, formatted_date
            else:
                return None, formatted_date
        except Exception as e:
            st.sidebar.warning(f"Error fetching data: {e}. Retrying...")
            time.sleep(1)  # Wait for 1 second before retrying
    
    return None, None

def display_fallback_content():
    st.write("We're currently unable to fetch game data. Here's some general NBA information:")
    st.write("- The NBA was founded on June 6, 1946.")
    st.write("- There are 30 teams in the NBA, divided into two conferences.")
    st.write("- The NBA season typically runs from October to April, followed by playoffs.")
    st.write("- The Boston Celtics have won the most NBA championships (17).")

def main():
    st.title("Welcome to the NBA Data App")
    st.write("This app provides information about NBA teams and players.")
    st.write("Use the sidebar to navigate between the Teams and Players sections.")

    # Add calendar to sidebar
    st.sidebar.subheader("Select Date")
    selected_date = st.sidebar.date_input("Choose a date", value=date.today())

    st.subheader(f"Games for {selected_date.strftime('%B %d, %Y')}")
    games, game_date = get_game_for_date(selected_date)
    
    if games is not None:
        if games:  # Check if the list is not empty
            for game in games:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.image(f"https://cdn.nba.com/logos/nba/{game['homeTeam']['teamId']}/global/L/logo.svg", width=100)
                    st.write(f"{game['homeTeam']['teamName']}")
                    st.write(f"Score: {game['homeTeam']['score']}")
                
                with col2:
                    st.write("VS")
                    game_status = game['gameStatus']
                    st.write(f"Status: {game_status}")
                
                with col3:
                    st.image(f"https://cdn.nba.com/logos/nba/{game['awayTeam']['teamId']}/global/L/logo.svg", width=100)
                    st.write(f"{game['awayTeam']['teamCity']} {game['awayTeam']['teamName']}")
                    st.write(f"Score: {game['awayTeam']['score']}")
                
                game_url = f"https://www.nba.com/game/{game['gameId']}"
                st.markdown(f"[View game details on NBA.com]({game_url})")
                
                st.write("---")  # Add a separator between games
        else:
            st.write("No games scheduled for the selected date.")
    else:
        st.error("Unable to fetch game data. Displaying fallback content.")
        display_fallback_content()

    st.subheader("Features")
    st.write("- View detailed information about NBA teams")
    st.write("- Explore current season stats for teams")
    st.write("- Check out player rosters and individual stats")
    st.write("- Analyze historical team performance")

if __name__ == "__main__":
    main()
