from st_supabase_connection import SupabaseConnection
import streamlit as st
import pandas as pd
from nba_api.live.nba.endpoints import scoreboard
from datetime import datetime

st.set_page_config(
    page_title="Basketboule",
    page_icon="🏀",
    layout="centered",
    menu_items={
        'About': 'https://github.com/slevin48/NBA'
    }
)

# Initialize Supabase connection
supabase = st.connection("supabase", type=SupabaseConnection)

# Functions

def calculate_win_probability(elo_a, elo_b):
    return 1 / (1 + 10 ** ((elo_b - elo_a) / 400))

def probability_to_odds(probability):
    return 1 / probability

# Fetch today's NBA games

# @st.cache_data(ttl=3600)  # Cache data for 1 hour
def get_today_games():
    today = datetime.now().date()
    date_str = today.strftime("%Y-%m-%d")
    
    # Load ELO ratings
    elo_df = pd.read_csv('elo-2023-24.csv')
    elo_dict = dict(zip(elo_df['Team'], elo_df['Elo']))
    
    board = scoreboard.ScoreBoard()
    games_today = board.games.get_dict()
    
    games = []
    for game in games_today:
        home_team = game['homeTeam']['teamName']
        away_team = game['awayTeam']['teamName']
        
        home_elo = elo_dict.get(home_team, 1500)  # Default ELO if not found
        away_elo = elo_dict.get(away_team, 1500)  # Default ELO if not found
        
        home_win_prob = round(calculate_win_probability(home_elo, away_elo), 2)
        away_win_prob = round(1 - home_win_prob, 2)
        game_info = {
            'Game ID': game['gameId'],
            'Date': date_str,
            'Home Team': game['homeTeam']['teamName'],
            'Away Team': game['awayTeam']['teamName'],
            'Home Team ID': str(game['homeTeam']['teamId']),
            'Away Team ID': str(game['awayTeam']['teamId']),
            'Home Odds': probability_to_odds(home_win_prob),
            'Away Odds': probability_to_odds(away_win_prob)
        }
        games.append(game_info)
    
    return pd.DataFrame(games)

# Initialize session state for bets
if 'bets' not in st.session_state:
    st.session_state['bets'] = []

# Initialize session state for user
if 'user' not in st.session_state:
    st.session_state['user'] = None

games = get_today_games()

# App Title
st.title("Basketboule")
st.subheader("Big Bets bring Big Bucks 🤑")

st.write("Games of the day")
if games.empty:
    st.info("There are no NBA games scheduled for today.")
else:
    # Define column configuration
    column_config = {
        "Date": st.column_config.DateColumn(
            "Date",
            help="Date",
            width="small",
        ),
        "Home Logo": st.column_config.ImageColumn(
            "Home Team",
            help="Home Logo",
            width="small",
        ),
        "Away Logo": st.column_config.ImageColumn(
            "Away Team",
            help="Away Logo",
            width="small",
        ),
        "Home Team": st.column_config.TextColumn(
            "Home Team",
            help="Home Team",
            width="small",
        ),
        "Away Team": st.column_config.TextColumn(
            "Away Team",
            help="Away Team",
            width="small",
        ),
        "Home Odds": st.column_config.NumberColumn(
            "Home Odds",
            help="Odds for the home team",
            format="%.2f",
        ),
        "Away Odds": st.column_config.NumberColumn(
            "Away Odds",
            help="Odds for the away team",
            format="%.2f",
        ),
    }

    # Prepare the dataframe with logo URLs
    display_df = games.copy()
    display_df['Home Logo'] = display_df.apply(lambda row: f"https://cdn.nba.com/logos/nba/{row['Home Team ID']}/global/L/logo.svg", axis=1)
    display_df['Away Logo'] = display_df.apply(lambda row: f"https://cdn.nba.com/logos/nba/{row['Away Team ID']}/global/L/logo.svg", axis=1)
    # Display the dataframe
    st.dataframe(
        display_df[['Date', 'Home Logo', 'Away Logo', 'Home Team', 'Away Team', 'Home Odds', 'Away Odds']],
        column_config=column_config,
        hide_index=True,
    )

# User Authentication Section
if st.session_state['user'] is None:
    st.write("<< Login in the sidebar to place a bet 💰")
    st.write("To get early access to the Basketboule betting app, email slevin.an209@gadz.org")
    with st.sidebar.form("Sign in"):
        st.write("**Log in**")
        # st.write("## Sign in")
        email = st.text_input(label="Enter your email ID")
        password = st.text_input(
            label="Enter your password",
            placeholder="Min 6 characters",
            type="password",
            help="Password is encrypted",
        )

        if st.form_submit_button('Login 🪄'):
            try:
                response = supabase.auth.sign_in_with_password(dict(email=email, password=password))
                auth_success_message = f"""Logged in. Welcome 🔓"""
                st.session_state['user'] = response.user

                # if response is not None:
                #     with st.expander("JSON response"):
                #         st.write(response.dict())

                if st.session_state['user']:
                    st.rerun()

            except Exception as e:
                st.error(str(e), icon="❌")

else:
    with st.sidebar:
        st.write(f"Welcome, {st.session_state['user'].email}!")
        if st.button("Logout"):
            supabase.auth.sign_out()
            st.session_state['user'] = None
            st.rerun()

    # Select a Game to Bet On
    st.subheader("Place a Bet")

    if games.empty:
        st.write("No betting opportunities today.")
    else:
        game_id = st.selectbox("Select Game", games['Game ID'], format_func=lambda x: f"{games[games['Game ID'] == x]['Home Team'].iloc[0]} vs {games[games['Game ID'] == x]['Away Team'].iloc[0]}")

        selected_game = games[games['Game ID'] == game_id].iloc[0]
        home_team = selected_game['Home Team']
        away_team = selected_game['Away Team']
        home_odds = selected_game['Home Odds']
        away_odds = selected_game['Away Odds']

        stake = st.number_input("Enter your stake ($)", min_value=1.0, step=1.0)

        team_choice = st.radio(
            "Choose a team to bet on:",
            (f"{home_team} (Odds: {home_odds:.2f})", f"{away_team} (Odds: {away_odds:.2f})")
        )

        # Modify the bet placement to include user ID
        if st.button("Place Bet"):
            bet = {
                'user_id': st.session_state['user'].id,
                'date': selected_game['Date'],
                'home_team': home_team,
                'away_team': away_team,
                'chosen_team': team_choice.split(" (")[0],
                'odds': home_odds if 'Home' in team_choice else away_odds,
                'stake': stake,
                'payout': stake * (home_odds if 'Home' in team_choice else away_odds)
            }
            # st.write(bet)
            # Insert bet into Supabase
            supabase.table("bets").insert(bet).execute()
            st.success("Bet placed successfully and stored in Supabase!")

    # Display Betting History (only for the logged-in user)
    st.header("Your Bets")

    # Fetch bets from Supabase for the current user
    bets_response = supabase.table("bets").select("*").eq("user_id", st.session_state['user'].id).execute()
    bets = bets_response.data

    if bets:
        bets_df = pd.DataFrame(bets)
        bets_df['date'] = pd.to_datetime(bets_df['date']).dt.strftime('%Y-%m-%d')
        bets_df = bets_df.drop(columns=['id', 'created_at', 'user_id'])
        st.dataframe(bets_df)
        # Summarize gains for the user
        total_gains = bets_df['payout'].sum()
        st.metric("Total Gains", f"${total_gains:.2f}")
    else:
        st.info("You haven't placed any bets yet.")

    # # Optional: Reset Bets (only for the current user)
    # if st.button("Reset Betting History"):
    #     supabase.table("bets").delete().eq("user_id", st.session_state['user'].id).execute()
    #     st.success("Your betting history has been reset in Supabase.")
