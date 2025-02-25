import streamlit as st
import random
import time
import requests
import json

# Initialize session state variables if they don't exist
if 'game_started' not in st.session_state:
    st.session_state.game_started = False
if 'players' not in st.session_state:
    st.session_state.players = []
if 'word' not in st.session_state:
    st.session_state.word = ""
if 'mr_white_index' not in st.session_state:
    st.session_state.mr_white_index = -1
if 'eliminated_players' not in st.session_state:
    st.session_state.eliminated_players = []
if 'round_number' not in st.session_state:
    st.session_state.round_number = 1
if 'current_phase' not in st.session_state:
    st.session_state.current_phase = "setup"
if 'scores' not in st.session_state:
    st.session_state.scores = {}
if 'mr_white_won_last' not in st.session_state:
    st.session_state.mr_white_won_last = False
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'generated_words' not in st.session_state:
    st.session_state.generated_words = []

# Function to generate a word using Gemini API
def generate_word_with_gemini(api_key):
    if not api_key:
        st.error("Please enter your Gemini API key")
        return None
        
    try:
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        headers = {
            "Content-Type": "application/json"
        }
        
        # Craft the prompt for Gemini to generate a single word for the game
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": "Generate a single random word that can be used as a location or concept for a social deduction game like 'Spyfall'. The word should be a common noun that most people would recognize. Just return the word and nothing else. Examples: Airport, Hospital, Restaurant, Wedding, University, Casino, etc."
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(f"{url}?key={api_key}", headers=headers, data=json.dumps(data))
        
        if response.status_code == 200:
            response_data = response.json()
            if 'candidates' in response_data and len(response_data['candidates']) > 0:
                if 'content' in response_data['candidates'][0]:
                    content = response_data['candidates'][0]['content']
                    if 'parts' in content and len(content['parts']) > 0:
                        word = content['parts'][0]['text'].strip()
                        # If the response has multiple words or punctuation, clean it to get just one word
                        if ' ' in word or '\n' in word:
                            word = word.split()[0].strip('.,!?;:')
                        return word
        
        st.error(f"Error generating word: {response.text}")
        return "Restaurant"  # Fallback word
    
    except Exception as e:
        st.error(f"Error when calling Gemini API: {str(e)}")
        return "School"  # Fallback word

# Function to reset the game
def reset_game():
    st.session_state.game_started = False
    st.session_state.players = []
    st.session_state.word = ""
    st.session_state.mr_white_index = -1
    st.session_state.eliminated_players = []
    st.session_state.round_number = 1
    st.session_state.current_phase = "setup"
    st.session_state.mr_white_won_last = False

# Function to start a new game
def start_game():
    if len(st.session_state.players) < 3:
        st.error("You need at least 3 players to start the game.")
        return
    
    st.session_state.game_started = True
    st.session_state.eliminated_players = []
    st.session_state.round_number = 1
    st.session_state.current_phase = "card_reveal"
    
    # Generate a word using Gemini API or use a previously generated one
    if st.session_state.generated_words:
        st.session_state.word = st.session_state.generated_words.pop(0)
    else:
        word = generate_word_with_gemini(st.session_state.api_key)
        if word:
            st.session_state.word = word
        else:
            st.error("Failed to generate a word. Please check your API key.")
            st.session_state.game_started = False
            return
    
    # Select a random player to be Mr. White
    st.session_state.mr_white_index = random.randint(0, len(st.session_state.players) - 1)

# Function to handle player elimination voting
def eliminate_player(player_index):
    eliminated_player = st.session_state.players[player_index]
    st.session_state.eliminated_players.append(eliminated_player)
    
    # Check if Mr. White was eliminated
    if player_index == st.session_state.mr_white_index:
        st.session_state.current_phase = "mr_white_guess"
    else:
        # If not all players except Mr. White are eliminated, continue to next round
        remaining_players = [p for i, p in enumerate(st.session_state.players) 
                             if p not in st.session_state.eliminated_players]
        if len(remaining_players) > 1:
            st.session_state.round_number += 1
            st.session_state.current_phase = "card_reveal"
        else:
            # Mr. White wins if they're the last one remaining
            st.session_state.current_phase = "game_over"
            st.session_state.mr_white_won_last = True
            update_scores(st.session_state.players[st.session_state.mr_white_index], True)

# Function to check Mr. White's guess
def check_mr_white_guess(guess):
    if guess.lower() == st.session_state.word.lower():
        st.session_state.mr_white_won_last = True
        update_scores(st.session_state.players[st.session_state.mr_white_index], True)
    else:
        st.session_state.mr_white_won_last = False
        # Update scores for all non-Mr. White players
        for i, player in enumerate(st.session_state.players):
            if i != st.session_state.mr_white_index:
                update_scores(player, True)
    
    st.session_state.current_phase = "game_over"

# Function to update player scores
def update_scores(player, won):
    if player not in st.session_state.scores:
        st.session_state.scores[player] = 0
    
    if won:
        st.session_state.scores[player] += 1

# Function to pre-generate words
def generate_multiple_words(api_key, count=5):
    words = []
    for _ in range(count):
        word = generate_word_with_gemini(api_key)
        if word:
            words.append(word)
    return words

# Main app layout
st.title("🕵️ Mr. White Game")

# Sidebar for game settings and API management
with st.sidebar:
    st.header("Game Settings")
    
    # Gemini API key input
    st.subheader("Gemini API Key")
    api_key = st.text_input("Enter your Gemini API key:", type="password", value=st.session_state.api_key)
    
    if api_key != st.session_state.api_key:
        st.session_state.api_key = api_key
        st.session_state.generated_words = []  # Clear any previously generated words
    
    # Pre-generate words button
    if st.session_state.api_key:
        if st.button("Pre-generate 5 words"):
            with st.spinner("Generating words..."):
                words = generate_multiple_words(st.session_state.api_key, 5)
                if words:
                    st.session_state.generated_words.extend(words)
                    st.success(f"Generated {len(words)} words for upcoming games!")
        
        # Show number of pre-generated words
        if st.session_state.generated_words:
            st.write(f"Pre-generated words available: {len(st.session_state.generated_words)}")
    
    # Scoreboard
    st.subheader("Scoreboard")
    if st.session_state.scores:
        sorted_scores = sorted(st.session_state.scores.items(), key=lambda x: x[1], reverse=True)
        for player, score in sorted_scores:
            st.write(f"{player}: {score} wins")
    else:
        st.write("No scores yet.")
    
    # Reset game button
    if st.button("Reset Game"):
        reset_game()

# Main game area
if not st.session_state.game_started:
    st.header("Game Setup")
    
    # API key warning
    if not st.session_state.api_key:
        st.warning("Please enter your Gemini API key in the sidebar to generate random words.")
    
    # Player management
    st.subheader("Players")
    
    # Display current players
    if st.session_state.players:
        st.write("Current players:")
        for i, player in enumerate(st.session_state.players):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"{i+1}. {player}")
            with col2:
                if st.button("Remove", key=f"remove_{i}"):
                    st.session_state.players.pop(i)
                    st.rerun()
    
    # Add new player
    new_player = st.text_input("Add a player:")
    if st.button("Add Player"):
        if new_player and new_player not in st.session_state.players:
            st.session_state.players.append(new_player)
            st.rerun()
        else:
            st.error("Please enter a valid player name that isn't already added.")
    
    # Start game button
    start_disabled = len(st.session_state.players) < 3 or not st.session_state.api_key
    start_help = "You need at least 3 players and a Gemini API key to start."
    
    if st.button("Start Game", disabled=start_disabled, help=start_help):
        start_game()
        st.rerun()
else:
    # Display game information
    st.header(f"Round {st.session_state.round_number}")
    
    # Display eliminated players
    if st.session_state.eliminated_players:
        st.write("Eliminated players: " + ", ".join(st.session_state.eliminated_players))
    
    # Card reveal phase
    if st.session_state.current_phase == "card_reveal":
        st.subheader("Card Reveal Phase")
        st.write("Each player should look at their card one at a time.")
        st.write("Pass the device to each player and let them click their name to see their card.")
        
        remaining_players = [p for p in st.session_state.players if p not in st.session_state.eliminated_players]
        
        for i, player in enumerate(st.session_state.players):
            if player not in st.session_state.eliminated_players:
                if st.button(f"I am {player}", key=f"card_{i}"):
                    # Show card to the player
                    with st.expander(f"{player}'s Card - ONLY {player} SHOULD LOOK", expanded=True):
                        if i == st.session_state.mr_white_index:
                            st.write("### You are Mr. White!")
                            st.write("Try to figure out the secret word by listening to others.")
                        else:
                            st.write(f"### Your word is: {st.session_state.word}")
                            st.write("Remember this word but do not reveal it directly!")
                        
                        time.sleep(0.5)  # Give them a moment to read
                        st.write("Close this section after you've read your card.")
        
        # Continue to voting phase button
        if st.button("Everyone has seen their cards - Continue to Discussion"):
            st.session_state.current_phase = "discussion"
            st.rerun()
    
    # Discussion phase
    elif st.session_state.current_phase == "discussion":
        st.subheader("Discussion Phase")
        st.write("Discuss the secret location without directly revealing the word.")
        st.write("Mr. White should try to blend in without knowing the word.")
        st.write("When the discussion is over, proceed to voting.")
        
        if st.button("Proceed to Voting"):
            st.session_state.current_phase = "voting"
            st.rerun()
    
    # Voting phase
    elif st.session_state.current_phase == "voting":
        st.subheader("Voting Phase")
        st.write("Vote for who you think is Mr. White:")
        
        remaining_players = [p for p in st.session_state.players if p not in st.session_state.eliminated_players]
        
        for i, player in enumerate(st.session_state.players):
            if player not in st.session_state.eliminated_players:
                if st.button(f"Eliminate {player}", key=f"vote_{i}"):
                    eliminate_player(i)
                    st.rerun()
    
    # Mr. White guess phase
    elif st.session_state.current_phase == "mr_white_guess":
        mr_white = st.session_state.players[st.session_state.mr_white_index]
        st.subheader(f"{mr_white} has been eliminated and was Mr. White!")
        st.write("Mr. White now has one chance to guess the word and win the game.")
        
        guess = st.text_input("Mr. White, what do you think the secret word was?")
        if st.button("Submit Guess"):
            check_mr_white_guess(guess)
            st.rerun()
    
    # Game over phase
    elif st.session_state.current_phase == "game_over":
        st.subheader("Game Over!")
        
        if st.session_state.mr_white_won_last:
            st.success(f"Mr. White ({st.session_state.players[st.session_state.mr_white_index]}) wins!")
            if st.session_state.current_phase == "game_over" and len(st.session_state.eliminated_players) < len(st.session_state.players) - 1:
                st.write("They successfully avoided being caught!")
            else:
                st.write(f"They correctly guessed the word: {st.session_state.word}")
        else:
            st.success("The group wins!")
            st.write(f"The word was: {st.session_state.word}")
            st.write(f"Mr. White was: {st.session_state.players[st.session_state.mr_white_index]}")
        
        # Generate next word in advance
        if len(st.session_state.generated_words) < 3 and st.session_state.api_key:
            with st.spinner("Generating word for next game..."):
                word = generate_word_with_gemini(st.session_state.api_key)
                if word:
                    st.session_state.generated_words.append(word)
        
        # Start a new game
        if st.button("Start a New Game"):
            st.session_state.game_started = False
            st.session_state.word = ""
            st.session_state.mr_white_index = -1
            st.session_state.eliminated_players = []
            st.session_state.round_number = 1
            st.session_state.current_phase = "setup"
            st.session_state.mr_white_won_last = False
            st.rerun()