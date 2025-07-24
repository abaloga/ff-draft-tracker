import streamlit as st
import pandas as pd
from datetime import datetime
import json
from draft_logic import DraftEngine
from player_data import PlayerDatabase
from utils import export_draft_state, import_draft_state, format_pick_number

# Configure Streamlit page
st.set_page_config(
    page_title="Fantasy Football Draft Assistant",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'draft_configured' not in st.session_state:
    st.session_state.draft_configured = False
if 'draft_engine' not in st.session_state:
    st.session_state.draft_engine = None
if 'player_db' not in st.session_state:
    st.session_state.player_db = PlayerDatabase()
if 'rosters_expanded' not in st.session_state:
    st.session_state.rosters_expanded = True

def main():
    # Sidebar for navigation and quick info
    with st.sidebar:
        st.header("Draft Control")
        
        if st.session_state.draft_configured:
            show_draft_sidebar_control()
        else:
            st.info("Configure your draft settings to begin!")
    
    # Main content area
    if not st.session_state.draft_configured:
        draft_configuration()
    else:
        draft_interface()

def draft_configuration():
    """Draft setup and configuration page"""
    st.header("⚙️ Draft Configuration")
    
    # Initialize session state for league configuration
    if 'league_size' not in st.session_state:
        st.session_state.league_size = 12
    if 'draft_position' not in st.session_state:
        st.session_state.draft_position = 1
    
    # League size selection outside form for reactivity
    st.subheader("League Settings")
    league_size = st.slider(
        "Number of Teams", 
        min_value=8, 
        max_value=16, 
        value=st.session_state.league_size,
        key="league_size_slider"
    )
    
    # Update session state and reset draft position if needed
    if league_size != st.session_state.league_size:
        old_league_size = st.session_state.league_size
        st.session_state.league_size = league_size
        # Reset draft position if it's invalid for new league size
        if st.session_state.draft_position > league_size:
            old_position = st.session_state.draft_position
            st.session_state.draft_position = 1
            st.warning(f"Draft position reset from {old_position} to 1 because the new league size ({league_size}) is smaller.")
    
    # Show current configuration
    col1, col2 = st.columns([1, 1])
    with col1:
        st.info(f"**League:** {league_size} teams")
    with col2:
        st.info(f"**Available positions:** 1-{league_size}")
    
    with st.form("draft_config"):
        # Create horizontal two-column layout
        col1, col2 = st.columns([1, 1])
        
        # Left Column: Draft Settings
        with col1:
            st.subheader("Draft Settings")
            
            # Draft position with dynamic max based on league size
            draft_position = st.slider(
                "Your Draft Position", 
                min_value=1, 
                max_value=league_size, 
                value=min(st.session_state.draft_position, league_size), 
                help=f"Select your draft position (1-{league_size})"
            )
            
            scoring_format = st.selectbox("Scoring Format", ["PPR", "Half-PPR", "Standard"])
            draft_type = st.selectbox("Draft Type", ["Snake", "Linear"])
        
        # Right Column: Roster Configuration
        with col2:
            st.subheader("Roster Configuration")
            
            qb_col1, qb_col2 = st.columns([3, 1])
            with qb_col1:
                st.write("Quarterback (QB):")
            with qb_col2:
                qb_spots = st.number_input("", min_value=1, max_value=3, value=1, key="qb", label_visibility="collapsed")
            
            rb_col1, rb_col2 = st.columns([3, 1])
            with rb_col1:
                st.write("Running Back (RB):")
            with rb_col2:
                rb_spots = st.number_input("", min_value=1, max_value=4, value=2, key="rb", label_visibility="collapsed")
            
            wr_col1, wr_col2 = st.columns([3, 1])
            with wr_col1:
                st.write("Wide Receiver (WR):")
            with wr_col2:
                wr_spots = st.number_input("", min_value=1, max_value=4, value=2, key="wr", label_visibility="collapsed")
            
            te_col1, te_col2 = st.columns([3, 1])
            with te_col1:
                st.write("Tight End (TE):")
            with te_col2:
                te_spots = st.number_input("", min_value=1, max_value=3, value=1, key="te", label_visibility="collapsed")
            
            flex_col1, flex_col2 = st.columns([3, 1])
            with flex_col1:
                st.write("FLEX (RB/WR/TE):")
            with flex_col2:
                flex_spots = st.number_input("", min_value=0, max_value=3, value=1, key="flex", label_visibility="collapsed")
            
            superflex_col1, superflex_col2 = st.columns([3, 1])
            with superflex_col1:
                st.write("FLEX (QB/RB/WR/TE):")
            with superflex_col2:
                superflex_spots = st.number_input("", min_value=0, max_value=3, value=0, key="superflex", label_visibility="collapsed")
            
            k_col1, k_col2 = st.columns([3, 1])
            with k_col1:
                st.write("Kicker (K):")
            with k_col2:
                k_spots = st.number_input("", min_value=0, max_value=2, value=1, key="k", label_visibility="collapsed")
            
            def_col1, def_col2 = st.columns([3, 1])
            with def_col1:
                st.write("Defense (DEF):")
            with def_col2:
                def_spots = st.number_input("", min_value=0, max_value=2, value=1, key="def", label_visibility="collapsed")
            
            bench_col1, bench_col2 = st.columns([3, 1])
            with bench_col1:
                st.write("Bench:")
            with bench_col2:
                bench_spots = st.number_input("", min_value=4, max_value=10, value=6, key="bench", label_visibility="collapsed")
        
        # Calculate total roster size and draft rounds (hidden calculation)
        total_roster = qb_spots + rb_spots + wr_spots + te_spots + flex_spots + superflex_spots + k_spots + def_spots + bench_spots
        total_rounds = total_roster
        
        # Full-width Start Draft button
        submitted = st.form_submit_button("🚀 Start Draft", type="primary", use_container_width=True)
        
        if submitted:
            # Update session state with selected values
            st.session_state.draft_position = draft_position
            
            # Validation: Ensure draft position is valid
            if draft_position > league_size:
                st.error(f"Draft position ({draft_position}) cannot be greater than number of teams ({league_size}). Please adjust your settings.")
                return
            
            # Create roster configuration
            roster_config = {
                'QB': qb_spots,
                'RB': rb_spots,
                'WR': wr_spots,
                'TE': te_spots,
                'FLEX': flex_spots,
                'SUPERFLEX': superflex_spots,
                'K': k_spots,
                'DEF': def_spots,
                'BENCH': bench_spots
            }
            
            # Initialize draft engine - use league_size from outside the form
            st.session_state.draft_engine = DraftEngine(
                league_size=league_size,
                user_position=draft_position,
                scoring_format=scoring_format,
                draft_type=draft_type,
                roster_config=roster_config,
                total_rounds=total_rounds
            )
            
            st.session_state.draft_configured = True
            st.rerun()

def draft_interface():
    """Tabbed draft interface with comprehensive draft view and draft board"""
    engine = st.session_state.draft_engine
    current_team = engine.get_current_team()
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["🎯 Live Draft", "📋 Draft Board"])
    
    with tab1:
        show_live_draft_view()
    
    with tab2:
        show_draft_board_view()

def show_draft_sidebar_control():
    """Display draft control information in the sidebar"""
    engine = st.session_state.draft_engine
    
    # Calculate pick within round
    picks_in_round = (engine.current_pick - 1) % engine.league_size + 1
    
    # Draft Overview
    st.markdown("**📊 Draft Overview**")
    st.divider()
    
    # Overall Pick
    st.markdown(f"**Overall Pick: {engine.current_pick}/{engine.total_picks}**")
    
    # Current Round
    st.markdown(f"**Round {engine.current_round}**")
    
    # Pick within round
    st.markdown(f"**Pick {picks_in_round}**")
    
    st.divider()
    
    # Show next few picks for user
    user_picks = engine.get_next_user_picks(3)
    if user_picks:
        picks_text = ", ".join([str(pick) for pick in user_picks])
        st.markdown(f"**🎯 Your next picks:** {picks_text}")
    else:
        st.markdown("**🎯 Your next picks:** None remaining")
    
    st.divider()
    
    # Reset button
    # Initialize confirmation state
    if 'show_reset_confirmation' not in st.session_state:
        st.session_state.show_reset_confirmation = False
    
    if not st.session_state.show_reset_confirmation:
        if st.button("🔄 Reset", type="secondary", key="reset_sidebar", use_container_width=True):
            st.session_state.show_reset_confirmation = True
            st.rerun()
    else:
        if st.button("✅ Confirm Reset", type="primary", key="confirm_reset_sidebar", use_container_width=True):
            st.session_state.draft_configured = False
            st.session_state.draft_engine = None
            st.session_state.show_reset_confirmation = False
            st.rerun()
    
    # Export button
    if st.button("💾 Export Draft", key="export_sidebar", use_container_width=True):
        draft_data = export_draft_state(st.session_state.draft_engine)
        st.download_button(
            "📥 Download",
            data=draft_data,
            file_name=f"draft_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            key="download_sidebar",
            use_container_width=True
        )

def show_live_draft_view():
    """Show the main live draft interface"""
    # Middle Section - Scrollable Mini Draft Board
    show_mini_draft_board()
    
    st.divider()
    
    # Bottom Row (Team Roster and Available Players) - Horizontal layout
    if st.session_state.rosters_expanded:
        # Normal layout when rosters are expanded - side by side
        bottom_col1, bottom_col2 = st.columns([1, 2])
        
        with bottom_col1:
            show_team_selection_and_roster()
        
        with bottom_col2:
            show_available_players(expanded=False)
    else:
        # Horizontal layout when rosters are minimized - thin sidebar + full width players
        bottom_col1, bottom_col2 = st.columns([0.1, 2.9])  # Very thin left column
        
        with bottom_col1:
            show_team_rosters_minimized()
        
        with bottom_col2:
            show_available_players(expanded=True)

def get_position_color(position):
    """Get the background color for a position"""
    position_colors = {
        'QB': '#6A1B9A',  # Purple
        'RB': '#2E7D32',  # Green
        'WR': '#1976D2',  # Blue
        'TE': '#E65100',  # Orange
        'K': '#5D4037',   # Brown
        'DEF': '#424242', # Dark Gray
        'FLEX': '#795548' # Medium Brown
    }
    return position_colors.get(position, '#757575')  # Default gray

def show_mini_draft_board():
    """Show a compact, scrollable draft board with 4 rounds context"""
    st.subheader("📋 Draft Progress")
    
    engine = st.session_state.draft_engine
    draft_board = engine.get_draft_board()
    
    # Create a dictionary for quick lookup of picks by position
    picks_by_position = {}
    for pick in draft_board:
        picks_by_position[pick['pick_number']] = pick
    
    # Determine which rounds to show (2 previous, current, next)
    current_round = engine.current_round
    start_round = max(1, current_round - 2)
    end_round = min(engine.total_rounds, current_round + 1)
    
    # Ensure we always show 4 rounds when possible
    if end_round - start_round < 3 and start_round > 1:
        start_round = max(1, end_round - 3)
    if end_round - start_round < 3 and end_round < engine.total_rounds:
        end_round = min(engine.total_rounds, start_round + 3)
    
    # Create header row with team numbers
    header_cols = st.columns([1] + [2] * engine.league_size)
    with header_cols[0]:
        st.markdown("<div style='text-align: center; font-size: 18px; font-weight: bold;'>Round</div>", unsafe_allow_html=True)
    for i in range(engine.league_size):
        with header_cols[i + 1]:
            team_num = i + 1
            if team_num == engine.user_position:
                # Highlight user's team column with background - larger and centered
                st.markdown(f"""
                <div style="
                    background-color: #E8F5E8;
                    border: 2px solid #4CAF50;
                    border-radius: 6px;
                    padding: 8px;
                    text-align: center;
                    margin: 2px 0;
                    font-size: 16px;
                    font-weight: bold;
                ">
                    Team {team_num} 🎯
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align: center; font-size: 16px; font-weight: bold;'>Team {team_num}</div>", unsafe_allow_html=True)
    
    # Create scrollable container for the draft board
    st.markdown("""
    <style>
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    .current-pick {
        animation: pulse 2s infinite;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create a container with limited height for 2 rounds only
    with st.container(height=200):
        # Create scrollable content
        for round_num in range(start_round, end_round + 1):
            round_cols = st.columns([1] + [2] * engine.league_size)
            
            # Round number column
            with round_cols[0]:
                if round_num == current_round:
                    st.markdown("**🎯**")
                else:
                    st.write(f"**{round_num}**")
            
            # Create round picks data
            round_picks = []
            for position_in_round in range(engine.league_size):
                pick_number = (round_num - 1) * engine.league_size + position_in_round + 1
                
                if engine.draft_type == 'snake' and round_num % 2 == 0:
                    team_num = engine.league_size - position_in_round
                else:
                    team_num = position_in_round + 1
                
                round_picks.append({
                    'pick_number': pick_number,
                    'team_num': team_num,
                    'position_in_round': position_in_round
                })
            
            # Display picks in each team's column
            for team_num in range(1, engine.league_size + 1):
                team_pick = None
                for pick_info in round_picks:
                    if pick_info['team_num'] == team_num:
                        team_pick = pick_info
                        break
                
                with round_cols[team_num]:
                    if team_pick:
                        pick_number = team_pick['pick_number']
                        
                        if pick_number in picks_by_position:
                            # Pick has been made
                            pick = picks_by_position[pick_number]
                            position_color = get_position_color(pick['position'])
                            
                            # Add user column highlighting
                            border_color = "#1B5E20" if pick['team'] == engine.user_position else "#424242"
                            border_width = "3px" if pick['team'] == engine.user_position else "2px"
                            
                            st.markdown(f"""
                            <div style="
                                border: {border_width} solid {border_color};
                                border-radius: 4px;
                                padding: 4px;
                                text-align: center;
                                background-color: {position_color};
                                color: white;
                                margin: 1px 0;
                                min-height: 45px;
                                font-size: 11px;
                                font-weight: bold;
                            ">
                                <strong>#{pick_number}</strong><br>
                                <strong>{pick['player_name'][:12]}{'...' if len(pick['player_name']) > 12 else ''}</strong><br>
                                <small>{pick['position']}</small>
                            </div>
                            """, unsafe_allow_html=True)
                                
                        elif pick_number == engine.current_pick:
                            # Current pick - red styling with user column highlighting
                            border_width = "4px" if team_num == engine.user_position else "3px"
                            
                            st.markdown(f"""
                            <div class="current-pick" style="
                                border: {border_width} solid #B71C1C;
                                border-radius: 4px;
                                padding: 4px;
                                text-align: center;
                                background-color: #F44336;
                                color: white;
                                margin: 1px 0;
                                min-height: 45px;
                                font-size: 11px;
                                font-weight: bold;
                            ">
                                <strong>#{pick_number}</strong><br>
                                <strong>NOW PICKING</strong><br>
                                <small>Team {team_num}</small>
                            </div>
                            """, unsafe_allow_html=True)
                            
                        else:
                            # Future pick
                            upcoming_pick_info = engine.get_pick_info(pick_number)
                            if upcoming_pick_info and upcoming_pick_info['is_user_pick']:
                                # User's upcoming pick - light green with dashed border
                                st.markdown(f"""
                                <div style="
                                    border: 3px dashed #2E7D32;
                                    border-radius: 4px;
                                    padding: 4px;
                                    text-align: center;
                                    background-color: #C8E6C9;
                                    color: black;
                                    margin: 1px 0;
                                    min-height: 45px;
                                    font-size: 11px;
                                    font-weight: bold;
                                ">
                                    <strong>#{pick_number}</strong><br>
                                    <strong>🎯 YOUR PICK</strong><br>
                                    <small>Team {team_num}</small>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                # Regular future pick with user column highlighting
                                border_color = "#2E7D32" if team_num == engine.user_position else "#757575"
                                border_width = "2px" if team_num == engine.user_position else "1px"
                                background_color = "#F1F8E9" if team_num == engine.user_position else "#E0E0E0"
                                
                                st.markdown(f"""
                                <div style="
                                    border: {border_width} dashed {border_color};
                                    border-radius: 4px;
                                    padding: 4px;
                                    text-align: center;
                                    background-color: {background_color};
                                    color: black;
                                    margin: 1px 0;
                                    min-height: 45px;
                                    font-size: 11px;
                                ">
                                    <strong>#{pick_number}</strong><br>
                                    <small>Team {team_num}</small>
                                </div>
                                """, unsafe_allow_html=True)
            
            # Add spacing between rounds if not the last round
            if round_num < end_round:
                st.write("")

def show_draft_board_view():
    """Show the draft board grid with all picks"""
    st.subheader("📋 Draft Board Overview")
    
    engine = st.session_state.draft_engine
    draft_board = engine.get_draft_board()
    
    # Create a dictionary for quick lookup of picks by position
    picks_by_position = {}
    for pick in draft_board:
        picks_by_position[pick['pick_number']] = pick
    
    # Display draft board grid - remove the info line
    
    # Create the grid using Streamlit columns
    # Header row with team numbers
    header_cols = st.columns([1] + [2] * engine.league_size)
    with header_cols[0]:
        st.markdown("<div style='text-align: center; font-size: 18px; font-weight: bold;'>Round</div>", unsafe_allow_html=True)
    for i in range(engine.league_size):
        with header_cols[i + 1]:
            team_num = i + 1
            if team_num == engine.user_position:
                # Highlight user's team column with background - larger and centered
                st.markdown(f"""
                <div style="
                    background-color: #E8F5E8;
                    border: 2px solid #4CAF50;
                    border-radius: 6px;
                    padding: 8px;
                    text-align: center;
                    margin: 2px 0;
                    font-size: 16px;
                    font-weight: bold;
                ">
                    Team {team_num} 🎯
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align: center; font-size: 16px; font-weight: bold;'>Team {team_num}</div>", unsafe_allow_html=True)
    
    st.divider()
    
    # Create rows for each round
    for round_num in range(1, engine.total_rounds + 1):
        round_cols = st.columns([1] + [2] * engine.league_size)
        
        # Round number column
        with round_cols[0]:
            st.write(f"**{round_num}**")
        
        # Create a list to store picks for this round in the correct chronological order
        round_picks = []
        
        # Get all picks for this round in chronological order
        for position_in_round in range(engine.league_size):
            # Calculate the overall pick number (this is chronological)
            pick_number = (round_num - 1) * engine.league_size + position_in_round + 1
            
            # Determine which team picks at this position in the round
            if engine.draft_type == 'snake' and round_num % 2 == 0:
                # Even rounds: Last team picks first, then second-to-last, etc. (snake draft)
                team_num = engine.league_size - position_in_round
            else:
                # Odd rounds (or linear draft): Team 1 picks first, then Team 2, etc.
                team_num = position_in_round + 1
            
            round_picks.append({
                'pick_number': pick_number,
                'team_num': team_num,
                'position_in_round': position_in_round
            })
        
        # Now display picks in each team's column
        for team_num in range(1, engine.league_size + 1):
            # Find the pick made by this team in this round
            team_pick = None
            for pick_info in round_picks:
                if pick_info['team_num'] == team_num:
                    team_pick = pick_info
                    break
            
            # Display in the team's column (team_num corresponds to column)
            with round_cols[team_num]:
                if team_pick:
                    pick_number = team_pick['pick_number']
                    
                    if pick_number in picks_by_position:
                        # Pick has been made
                        pick = picks_by_position[pick_number]
                        position_color = get_position_color(pick['position'])
                        
                        # Add user column highlighting
                        border_color = "#1B5E20" if pick['team'] == engine.user_position else "#424242"
                        border_width = "3px" if pick['team'] == engine.user_position else "2px"
                        
                        st.markdown(f"""
                        <div style="
                            border: {border_width} solid {border_color};
                            border-radius: 6px;
                            padding: 8px;
                            text-align: center;
                            background-color: {position_color};
                            color: white;
                            margin: 2px 0;
                            min-height: 60px;
                            font-weight: bold;
                        ">
                            <small><strong>#{pick_number}</strong></small><br>
                            <strong>{pick['player_name']}</strong><br>
                            <small>{pick['position']} - {pick.get('nfl_team', 'N/A')}</small>
                        </div>
                        """, unsafe_allow_html=True)
                            
                    elif pick_number == engine.current_pick:
                        # Current pick - red styling with user column highlighting
                        border_width = "4px" if team_num == engine.user_position else "3px"
                        
                        st.markdown(f"""
                        <div style="
                            border: {border_width} solid #B71C1C;
                            border-radius: 6px;
                            padding: 8px;
                            text-align: center;
                            background-color: #F44336;
                            color: white;
                            margin: 2px 0;
                            min-height: 60px;
                            font-weight: bold;
                        ">
                            <small><strong>#{pick_number}</strong></small><br>
                            <strong>CURRENT PICK</strong><br>
                            <small>Team {team_num}</small>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    else:
                        # Future pick - light gray styling
                        upcoming_pick_info = engine.get_pick_info(pick_number)
                        if upcoming_pick_info and upcoming_pick_info['is_user_pick']:
                            # User's upcoming pick - light green with dashed border
                            st.markdown(f"""
                            <div style="
                                border: 3px dashed #2E7D32;
                                border-radius: 6px;
                                padding: 8px;
                                text-align: center;
                                background-color: #C8E6C9;
                                color: black;
                                margin: 2px 0;
                                min-height: 60px;
                                font-weight: bold;
                            ">
                                <small><strong>#{pick_number}</strong></small><br>
                                <small>🎯 YOUR PICK</small><br>
                                <small>Team {team_num}</small>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            # Regular future pick with user column highlighting
                            border_color = "#2E7D32" if team_num == engine.user_position else "#757575"
                            border_width = "2px" if team_num == engine.user_position else "1px"
                            background_color = "#F1F8E9" if team_num == engine.user_position else "#E0E0E0"
                            
                            st.markdown(f"""
                            <div style="
                                border: {border_width} dashed {border_color};
                                border-radius: 6px;
                                padding: 8px;
                                text-align: center;
                                background-color: {background_color};
                                color: black;
                                margin: 2px 0;
                                min-height: 60px;
                            ">
                                <small><strong>#{pick_number}</strong></small><br>
                                <small>Team {team_num}</small>
                            </div>
                            """, unsafe_allow_html=True)

def show_team_rosters_minimized():
    """Show a minimized vertical sidebar for team rosters with expand button"""
    # Create a vertical sidebar with expand button
    st.markdown("""
    <div style="
        background-color: #E8F5E8;
        border: 2px solid #4CAF50;
        border-radius: 6px;
        padding: 8px 4px;
        text-align: center;
        height: 350px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        margin: 0;
    ">
        <div style="
            writing-mode: vertical-rl;
            text-orientation: mixed;
            font-weight: bold;
            font-size: 14px;
            color: #2E7D32;
            margin-bottom: 20px;
        ">
            👥 Team Rosters
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Expand button positioned below the sidebar
    st.write("")  # Add some space
    if st.button("📋", help="Expand team rosters to full view", key="expand_rosters", use_container_width=True):
        st.session_state.rosters_expanded = True
        st.rerun()

def show_team_selection_and_roster():
    """Show team selection dropdown and roster for selected team"""
    # Add horizontal collapse button
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.subheader("👥 Team Rosters")
    
    with col2:
        if st.button("◀️", help="Collapse to sidebar", key="minimize_rosters"):
            st.session_state.rosters_expanded = False
            st.rerun()
    
    engine = st.session_state.draft_engine
    
    # Team selection dropdown
    team_options = [f"Team {i}" for i in range(1, engine.league_size + 1)]
    selected_team_idx = st.selectbox(
        "Select Team to View",
        range(len(team_options)),
        format_func=lambda x: team_options[x],
        index=engine.user_position - 1  # Default to user's team
    )
    selected_team = selected_team_idx + 1
    
    # Highlight if it's user's team
    if selected_team == engine.user_position:
        st.info("🎯 This is your team")
    
    # Show roster for selected team
    roster = engine.get_team_roster(selected_team)
    
    if not roster:
        st.write("No players drafted yet")
        return
    
    # Group players by position
    position_groups = {}
    for player in roster:
        pos = player['position']
        if pos not in position_groups:
            position_groups[pos] = []
        position_groups[pos].append(player)
    
    # Display roster by position
    positions = ['QB', 'RB', 'WR', 'TE', 'FLEX', 'SUPERFLEX', 'K', 'DEF']
    
    for pos in positions:
        if pos in position_groups:
            st.write(f"**{pos}:**")
            for player in position_groups[pos]:
                st.write(f"• {player['player_name']} ({player.get('nfl_team', 'N/A')})")
        else:
            # Show empty slots
            required_spots = engine.roster_config.get(pos, 0)
            if required_spots > 0:
                st.write(f"**{pos}:** *({required_spots} open)*")
    
    # Show bench players
    bench_players = [p for p in roster if p['position'] not in positions]
    if bench_players:
        st.write("**BENCH:**")
        for player in bench_players:
            st.write(f"• {player['player_name']} ({player['position']}) - {player.get('nfl_team', 'N/A')}")


def show_available_players(expanded=False):
    """Display available players with optimized layout"""
    # Add expanded indicator when in full width mode
    if expanded or not st.session_state.rosters_expanded:
        st.subheader("🎯 Available Players (Expanded View)")
    else:
        st.subheader("🎯 Available Players")
    
    player_db = st.session_state.player_db
    drafted_players = st.session_state.draft_engine.get_drafted_players()
    
    # Compact filter row
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search Player Name", placeholder="Type player name...")
    
    with col2:
        position_filter = st.selectbox(
            "Position", 
            ["All"] + ["QB", "RB", "WR", "TE", "K", "DEF"]
        )
    
    with col3:
        team_filter = st.selectbox(
            "NFL Team",
            ["All"] + player_db.get_nfl_teams()
        )
    
    with col4:
        show_count = st.selectbox("Show", [25, 50, 100], index=1)
    
    # Get filtered players
    available_players = player_db.get_available_players(
        drafted_players=drafted_players,
        search_term=search_term,
        position_filter=position_filter if position_filter != "All" else None,
        team_filter=team_filter if team_filter != "All" else None
    )
    
    if available_players.empty:
        st.warning("No players match your current filters.")
        return
    
    # Create a more compact table-like display
    st.write(f"**{len(available_players)} players available** (showing top {show_count})")
    
    # Header row
    header_cols = st.columns([3, 1, 1, 1, 1, 1])
    with header_cols[0]:
        st.write("**Player**")
    with header_cols[1]:
        st.write("**Pos**")
    with header_cols[2]:
        st.write("**Team**")
    with header_cols[3]:
        st.write("**Rank**")
    with header_cols[4]:
        st.write("**Proj**")
    with header_cols[5]:
        st.write("**Action**")
    
    st.divider()
    
    # Display players in compact rows
    for idx, player in available_players.head(show_count).iterrows():
        col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 1])
        
        with col1:
            st.write(f"**{player['name']}**")
        
        with col2:
            st.write(player['position'])
        
        with col3:
            st.write(player['team'])
        
        with col4:
            st.write(f"#{player.get('rank', 'N/A')}")
        
        with col5:
            st.write(player.get('projected_points', 'N/A'))
        
        with col6:
            if st.button(f"Draft", key=f"draft_{player['id']}"):
                draft_player(player)

def draft_player(player):
    """Draft a player to the current team"""
    engine = st.session_state.draft_engine
    current_team = engine.get_current_team()
    
    success = engine.draft_player(
        player_id=player['id'],
        player_name=player['name'],
        position=player['position'],
        team=current_team,
        nfl_team=player['team']
    )
    
    if success:
        st.success(f"Drafted {player['name']} to Team {current_team}!")
        st.rerun()
    else:
        st.error("Error drafting player. Please try again.")

def display_roster(roster, roster_config, compact=False):
    """Display a team's roster"""
    if not roster:
        st.write("No players drafted yet")
        return
    
    # Group by position
    by_position = {}
    for player in roster:
        pos = player['position']
        if pos not in by_position:
            by_position[pos] = []
        by_position[pos].append(player)
    
    # Display by position groups
    for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']:
        if pos in by_position:
            if not compact:
                st.write(f"**{pos}:**")
            for player in by_position[pos]:
                if compact:
                    st.write(f"{pos}: {player['player_name']}")
                else:
                    st.write(f"- {player['player_name']} ({player.get('nfl_team', 'N/A')})")

if __name__ == "__main__":
    main()
