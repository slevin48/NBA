import streamlit as st
from nba_api.stats.endpoints import playercareerstats
from requests.exceptions import ReadTimeout, TooManyRedirects, ConnectionError
import time
from functools import partial

@st.cache_data(ttl=3600)  # Cache data for 1 hour
def fetch_data(endpoint, **kwargs):
    max_retries = 5
    base_delay = 3  # seconds
    
    for i in range(max_retries):
        try:
            # Increase timeout to 60 seconds
            endpoint_with_timeout = partial(endpoint, timeout=60)
            return endpoint_with_timeout(**kwargs).get_data_frames()[0]
        except (ReadTimeout, ConnectionError, TooManyRedirects) as e:
            if i < max_retries - 1:
                delay = base_delay * (2 ** i)  # Exponential backoff
                print(f"Request failed, retrying in {delay} seconds... (Attempt {i+1}/{max_retries})")
                time.sleep(delay)
            else:
                print(f"Failed to fetch data after {max_retries} attempts. Please try again later.")
                return None

@st.cache_data(ttl=86400)  # Cache player stats for 24 hours
def fetch_player_stats(player_id):
    return fetch_data(playercareerstats.PlayerCareerStats, player_id=player_id)
