from st_supabase_connection import SupabaseConnection
import streamlit as st
import pandas as pd
from utils import get_live_games, calculate_win_probability, probability_to_odds
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

# Fetch today's NBA games

# @st.cache_data(ttl=3600)  # Cache data for 1 hour
def format_games():
    
    # Load ELO ratings
    elo_df = pd.read_csv('elo-2023-24.csv')
    elo_dict = dict(zip(elo_df['Team'], elo_df['Elo']))
    
    last_games = get_live_games()
    
    games = []
    for _, game in last_games.iterrows():
        home_team = game['homeTeamName']
        away_team = game['awayTeamName']
        
        home_elo = elo_dict.get(home_team, 1500)  # Default ELO if not found
        away_elo = elo_dict.get(away_team, 1500)  # Default ELO if not found
        
        home_win_prob = round(calculate_win_probability(home_elo, away_elo), 2)
        away_win_prob = round(1 - home_win_prob, 2)
        game_info = {
            'Game ID': game['gameId'],
            'Home Team': game['homeTeamName'],
            'Away Team': game['awayTeamName'],
            'Home Team ID': str(game['homeTeamId']),
            'Away Team ID': str(game['awayTeamId']),
            'Home Odds': probability_to_odds(home_win_prob),
            'Away Odds': probability_to_odds(away_win_prob),
            'Status': game['gameStatusText']
        }
        games.append(game_info)
    
    return pd.DataFrame(games)

# Initialize session state for bets
if 'bets' not in st.session_state:
    st.session_state['bets'] = []

# Initialize session state for user
if 'user' not in st.session_state:
    st.session_state['user'] = None

games = format_games()

# App Title
st.title("Basketboule")
st.sidebar.subheader("Big Bets bring Big Bucks 🤑")
st.subheader("NBA Betting Simulator")

st.write("Games of the day")
if games.empty:
    st.info("There are no NBA games scheduled for today.")
else:
    # Define column configuration
    column_config = {
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
        "Status": st.column_config.TextColumn(
            "Status",
            help="Status of the game",
            width="small",
        ),
        "Game Link": st.column_config.LinkColumn(
            "NBA Game",
            help="Link to NBA game",
            width="small",
            display_text="Watch 🏀"  # This will be the text shown for all links
        ),
    }

    # Prepare the dataframe with logo URLs and game links
    display_df = games.copy()
    display_df['Home Logo'] = display_df.apply(lambda row: f"https://cdn.nba.com/logos/nba/{row['Home Team ID']}/global/L/logo.svg", axis=1)
    display_df['Away Logo'] = display_df.apply(lambda row: f"https://cdn.nba.com/logos/nba/{row['Away Team ID']}/global/L/logo.svg", axis=1)
    display_df['Game Link'] = display_df.apply(lambda row: f"https://www.nba.com/game/{row['Game ID']}", axis=1)
    
    # Display the dataframe
    st.dataframe(
        display_df[['Home Logo', 'Away Logo', 'Home Team', 'Away Team', 'Home Odds', 'Away Odds', 'Status', 'Game Link']],
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

        # Place Bet button logic
        if st.button("Place Bet"):
            # Determine which team was chosen and get corresponding odds
            chosen_team = team_choice.split(" (")[0]  # Get just the team name
            chosen_odds = float(team_choice.split("Odds: ")[1].strip(")"))  # Extract odds value
            
            bet = {
                'user_id': st.session_state['user'].id,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'home_team': home_team,
                'away_team': away_team,
                'chosen_team': chosen_team,
                'odds': chosen_odds,
                'stake': stake,
                'payout': stake * chosen_odds
            }
            
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
