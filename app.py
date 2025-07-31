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
    
    # Create 3-column equal width layout
    col1, col2, col3 = st.columns([1, 1, 1])
    
    # Column 1 - Team Settings & Draft Configuration
    with col1:
        st.subheader("Team Settings & Draft")
        
        # Number of Teams - 4 buttons in a row
        st.write("**Number of Teams:**")
        team_cols = st.columns(4)
        team_options = [8, 10, 12, 16]
        
        for i, team_count in enumerate(team_options):
            with team_cols[i]:
                button_type = "primary" if st.session_state.league_size == team_count else "secondary"
                button_label = f"{team_count}" if st.session_state.league_size == team_count else str(team_count)
                if st.button(button_label, key=f"team_{team_count}", type=button_type, use_container_width=True):
                    # Update league size and reset draft position if needed
                    if st.session_state.draft_position > team_count:
                        st.session_state.draft_position = 1
                    st.session_state.league_size = team_count
                    st.rerun()
        
        league_size = st.session_state.league_size
        
        st.write("")  # Add spacing
        
        # Draft Position - Dynamic button grid (4 buttons per row)
        st.write(f"**Your Draft Position:** (Select 1-{league_size})")
        position_rows = (league_size + 3) // 4  # Calculate number of rows needed
        
        for row in range(position_rows):
            pos_cols = st.columns(4)
            for col in range(4):
                position = row * 4 + col + 1
                if position <= league_size:
                    with pos_cols[col]:
                        button_type = "primary" if st.session_state.draft_position == position else "secondary"
                        if st.button(str(position), key=f"pos_{position}", type=button_type, use_container_width=True):
                            st.session_state.draft_position = position
                            st.rerun()
        
        draft_position = st.session_state.draft_position
        
        st.write("")  # Add spacing
        
        # Scoring Format and Draft Type
        scoring_format = st.selectbox("Scoring Format", ["PPR", "Half-PPR", "Standard"])
        draft_type = st.selectbox("Draft Type", ["Snake", "Linear"])
        
        st.write("")  # Add spacing
        
        # Start Draft Button - Full width of this column only
        if st.button("Start Draft", type="primary", use_container_width=True):
            # Validation
            if draft_position > league_size:
                st.error(f"Draft position ({draft_position}) cannot be greater than number of teams ({league_size}). Please adjust your settings.")
            else:
                # Get roster configuration from column 2 session state
                roster_config = {
                    'QB': st.session_state.get('qb_spots', 1),
                    'RB': st.session_state.get('rb_spots', 2),
                    'WR': st.session_state.get('wr_spots', 2),
                    'TE': st.session_state.get('te_spots', 1),
                    'FLEX': st.session_state.get('flex_spots', 1),
                    'SUPERFLEX': st.session_state.get('superflex_spots', 0),
                    'K': st.session_state.get('k_spots', 1),
                    'DEF': st.session_state.get('def_spots', 1),
                    'BENCH': st.session_state.get('bench_spots', 6)
                }
                
                total_rounds = sum(roster_config.values())
                
                # Initialize draft engine
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
    
    # Column 2 - Roster Configuration
    with col2:
        st.subheader("Roster Configuration")
        
        # Initialize roster spots in session state if not present
        if 'qb_spots' not in st.session_state:
            st.session_state.qb_spots = 1
        if 'rb_spots' not in st.session_state:
            st.session_state.rb_spots = 2
        if 'wr_spots' not in st.session_state:
            st.session_state.wr_spots = 2
        if 'te_spots' not in st.session_state:
            st.session_state.te_spots = 1
        if 'flex_spots' not in st.session_state:
            st.session_state.flex_spots = 1
        if 'superflex_spots' not in st.session_state:
            st.session_state.superflex_spots = 0
        if 'k_spots' not in st.session_state:
            st.session_state.k_spots = 1
        if 'def_spots' not in st.session_state:
            st.session_state.def_spots = 1
        if 'bench_spots' not in st.session_state:
            st.session_state.bench_spots = 6
        
        # Helper function for +/- buttons
        def roster_position_selector(position_name, key, min_val, max_val, current_val):
            pos_col1, pos_col2, pos_col3, pos_col4 = st.columns([2.5, 0.6, 0.4, 0.6])
            with pos_col1:
                st.write(f"**{position_name}:**")
            with pos_col2:
                # Make - button more visible with explicit styling
                minus_disabled = current_val <= min_val
                if st.button("➖", key=f"minus_{key}", disabled=minus_disabled, use_container_width=True, 
                           help="Decrease" if not minus_disabled else "At minimum"):
                    st.session_state[key] = max(min_val, current_val - 1)
                    st.rerun()
            with pos_col3:
                # Center the current value display
                st.markdown(f"<div style='text-align: center; padding: 8px; font-weight: bold; font-size: 16px; background-color: #262730; border-radius: 4px;'>{current_val}</div>", 
                           unsafe_allow_html=True)
            with pos_col4:
                # Make + button more visible with explicit styling
                plus_disabled = current_val >= max_val
                if st.button("➕", key=f"plus_{key}", disabled=plus_disabled, use_container_width=True,
                           help="Increase" if not plus_disabled else "At maximum"):
                    st.session_state[key] = min(max_val, current_val + 1)
                    st.rerun()
            
            return current_val
        
        # Roster positions with +/- buttons
        qb_spots = roster_position_selector("Quarterback (QB)", "qb_spots", 0, 3, st.session_state.qb_spots)
        rb_spots = roster_position_selector("Running Back (RB)", "rb_spots", 0, 4, st.session_state.rb_spots)
        wr_spots = roster_position_selector("Wide Receiver (WR)", "wr_spots", 0, 4, st.session_state.wr_spots)
        te_spots = roster_position_selector("Tight End (TE)", "te_spots", 0, 3, st.session_state.te_spots)
        flex_spots = roster_position_selector("FLEX (RB/WR/TE)", "flex_spots", 0, 3, st.session_state.flex_spots)
        superflex_spots = roster_position_selector("SUPERFLEX (QB/RB/WR/TE)", "superflex_spots", 0, 3, st.session_state.superflex_spots)
        k_spots = roster_position_selector("Kicker (K)", "k_spots", 0, 2, st.session_state.k_spots)
        def_spots = roster_position_selector("Defense (DEF)", "def_spots", 0, 2, st.session_state.def_spots)
        bench_spots = roster_position_selector("Bench (BEN)", "bench_spots", 0, 10, st.session_state.bench_spots)
        
        # Show total roster size
        total_roster = qb_spots + rb_spots + wr_spots + te_spots + flex_spots + superflex_spots + k_spots + def_spots + bench_spots
        st.write("")
        st.info(f"**Total Roster Size:** {total_roster} players")
    
    # Column 3 - Placeholder
    with col3:
        st.subheader("Draft Summary")
        
        # Show current selections
        st.info(f"**League Size:** {st.session_state.league_size} teams")
        st.info(f"**Your Position:** #{st.session_state.draft_position}")
        
        # Calculate and show total roster
        total_spots = (st.session_state.get('qb_spots', 1) + st.session_state.get('rb_spots', 2) + 
                      st.session_state.get('wr_spots', 2) + st.session_state.get('te_spots', 1) + 
                      st.session_state.get('flex_spots', 1) + st.session_state.get('superflex_spots', 0) + 
                      st.session_state.get('k_spots', 1) + st.session_state.get('def_spots', 1) + 
                      st.session_state.get('bench_spots', 6))
        
        st.info(f"**Draft Rounds:** {total_spots}")
        
        st.write("")
        st.write("**Coming Soon:**")
        st.write("• Import/Export drafts")
        st.write("• Custom player rankings")
        st.write("• Draft timer")
        st.write("• Mock draft mode")

def draft_interface():
    """Tabbed draft interface with comprehensive draft view and draft board"""
    engine = st.session_state.draft_engine
    current_team = engine.get_current_team()
    
    # Create tabs for different views with enhanced styling
    tab1, tab2 = st.tabs(["**Live Draft**", "**Draft Board**"])
    
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
    st.write(" ")  # Add spacing
    
    # Overall Pick
    st.markdown(f"**Overall Pick: {engine.current_pick}/{engine.total_picks}**")
    
    # Current Round
    st.markdown(f"**Round {engine.current_round}**")
    
    # Pick within round
    st.markdown(f"**Pick {picks_in_round}**")
    
    st.write(" ")  # Add spacing
    
    # Show next few picks for user
    user_picks = engine.get_next_user_picks(4)
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
    
    st.write("")

    # Bottom Row (Available Players and Team Roster) - Horizontal layout
    if st.session_state.rosters_expanded:
        # Normal layout when rosters are expanded - side by side
        # Adjusted ratio to give more space to Available Players (3:1 instead of 2:1)
        bottom_col1, bottom_col2 = st.columns([3, 1])
        
        with bottom_col1:
            show_available_players(expanded=False)
        
        with bottom_col2:
            show_team_selection_and_roster()
    else:
        # Horizontal layout when rosters are minimized - full width players + thin right sidebar
        bottom_col1, bottom_col2 = st.columns([2.9, 0.1])  # Very thin right column
        
        with bottom_col1:
            show_available_players(expanded=True)
        
        with bottom_col2:
            show_team_rosters_minimized()

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
                    background-color: #2E7D3225;
                    border: 2px solid #2E7D32;
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

    # Create a container for the draft board
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
    
    # Create a container with limited height for all rounds
    with st.container(height=350):
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
                                    <br>
                                    <strong>Team {team_num}</strong><br>
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
                    background-color: #2E7D3225;
                    border: 2px solid #2E7D32;
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
    """Show a minimized vertical sidebar for team rosters with expand button on the right"""
    # Expand button positioned at the top
    if st.button("◀", help="Expand team rosters to full view", key="expand_rosters", use_container_width=True):
        st.session_state.rosters_expanded = True
        st.rerun()
    
    # Create a vertical sidebar below the button
    st.markdown("""
    <div style="
        background-color: #2E7D3225;
        border: 2px solid #2E7D32;
        border-radius: 6px;
        padding: 8px 4px;
        text-align: center;
        height: 300px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        margin: 0;
        margin-top: 8px;
    ">
        <div style="
            writing-mode: vertical-rl;
            text-orientation: mixed;
            font-weight: bold;
            font-size: 14px;
            color: #2E7D32;
        ">
            Team Rosters
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_team_selection_and_roster():
    """Show team selection dropdown and roster for selected team with smart position assignment"""
    # Integrated header with collapse button and team dropdown on same line
    col1, col2, col3 = st.columns([0.5, 2, 2])
    
    with col1:
        if st.button("▶", help="Collapse to sidebar", key="minimize_rosters"):
            st.session_state.rosters_expanded = False
            st.rerun()
    
    with col2:
        st.subheader("Team Rosters")
    
    with col3:
        engine = st.session_state.draft_engine
        # Team selection dropdown inline with header
        team_options = [f"Team {i}" for i in range(1, engine.league_size + 1)]
        selected_team_idx = st.selectbox(
            "Select Team:",
            range(len(team_options)),
            format_func=lambda x: team_options[x],
            index=engine.user_position - 1,  # Default to user's team
            key="team_dropdown",
            label_visibility="collapsed"
        )
        selected_team = selected_team_idx + 1
    
    # Get roster for selected team
    roster = engine.get_team_roster(selected_team)
    
    # Smart position assignment logic (works with empty rosters too)
    assigned_roster = assign_players_to_positions(roster, engine.roster_config)
    
    # Display roster hierarchically
    display_hierarchical_roster(assigned_roster, engine.roster_config)

def assign_players_to_positions(roster, roster_config):
    """
    Smart position assignment logic that assigns players to optimal roster positions
    Priority: Most specific position → FLEX/SUPERFLEX → Bench
    """
    # Create empty roster structure
    assigned_roster = create_empty_roster_structure(roster_config)
    
    # If no roster or empty roster, return empty structure
    if not roster:
        return assigned_roster
    
    # Group players by their original position
    players_by_position = {}
    for player in roster:
        pos = player['position']
        if pos not in players_by_position:
            players_by_position[pos] = []
        players_by_position[pos].append(player)
    
    # Assignment priority order
    def assign_player_to_slot(player, player_position):
        """Try to assign a player to the best available slot"""
        
        # 1. Most specific position first
        if player_position in ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']:
            # Try primary position slots first
            for i in range(roster_config.get(player_position, 0)):
                if assigned_roster['starting_lineup'][player_position][i] is None:
                    assigned_roster['starting_lineup'][player_position][i] = player
                    return True
        
        # 2. FLEX positions second (for RB/WR/TE)
        if player_position in ['RB', 'WR', 'TE'] and roster_config.get('FLEX', 0) > 0:
            for i in range(roster_config['FLEX']):
                if assigned_roster['starting_lineup']['FLEX'][i] is None:
                    assigned_roster['starting_lineup']['FLEX'][i] = player
                    return True
        
        # 3. SUPERFLEX positions third (for QB/RB/WR/TE)
        if player_position in ['QB', 'RB', 'WR', 'TE'] and roster_config.get('SUPERFLEX', 0) > 0:
            for i in range(roster_config['SUPERFLEX']):
                if assigned_roster['starting_lineup']['SUPERFLEX'][i] is None:
                    assigned_roster['starting_lineup']['SUPERFLEX'][i] = player
                    return True
        
        # 4. Bench last
        for i in range(roster_config.get('BENCH', 0)):
            if assigned_roster['bench'][i] is None:
                assigned_roster['bench'][i] = player
                return True
        
        return False
    
    # Assign players in order of specificity (most specific positions first)
    position_priority = ['K', 'DEF', 'QB', 'TE', 'RB', 'WR']
    
    for position in position_priority:
        if position in players_by_position:
            for player in players_by_position[position]:
                assign_player_to_slot(player, position)
    
    return assigned_roster

def create_empty_roster_structure(roster_config):
    """Create an empty roster structure based on configuration"""
    roster_structure = {
        'starting_lineup': {},
        'bench': [None] * roster_config.get('BENCH', 0)
    }
    
    # Initialize starting lineup positions
    for position in ['QB', 'RB', 'WR', 'TE', 'FLEX', 'SUPERFLEX', 'K', 'DEF']:
        slot_count = roster_config.get(position, 0)
        if slot_count > 0:
            roster_structure['starting_lineup'][position] = [None] * slot_count
    
    return roster_structure

def display_hierarchical_roster(assigned_roster, roster_config):
    """Display roster in hierarchical position-based layout"""
    
    # Position display order - using shorthand labels
    position_labels = {
        'QB': 'QB',
        'RB': 'RB', 
        'WR': 'WR',
        'TE': 'TE',
        'FLEX': 'FLEX',
        'SUPERFLEX': 'SUPERFLEX',
        'K': 'K',
        'DEF': 'DEF'
    }
    
    for position in ['QB', 'RB', 'WR', 'TE', 'FLEX', 'SUPERFLEX', 'K', 'DEF']:
        if position in assigned_roster['starting_lineup']:
            slots = assigned_roster['starting_lineup'][position]
            slot_count = len(slots)
            
            if slot_count == 1:
                # Single slot position
                display_position_slot(position_labels[position], slots[0], position)
            else:
                # Multiple slot position - no numbering, just repeat the position name
                for i, player in enumerate(slots):
                    display_position_slot(position_labels[position], player, position)
    
    # Bench positions - no section header
    if roster_config.get('BENCH', 0) > 0:
        bench_slots = assigned_roster['bench']
        
        for i, player in enumerate(bench_slots):
            display_position_slot("BN", player, 'BENCH')

def display_position_slot(slot_label, player, position_type):
    """Display a single position slot with player card or empty placeholder"""
    
    if player is not None:
        # Player card styling with full width and position label inside
        position_color = get_position_color(player['position'])
        
        st.markdown(f"""
        <div style="
            border: 2px solid {position_color};
            border-radius: 8px;
            padding: 8px 12px;
            background: linear-gradient(135deg, {position_color}15, {position_color}25);
            margin: 2px 0;
            display: flex;
            align-items: center;
            min-height: 45px;
            width: 100%;
        ">
            <div style="
                background-color: {position_color};
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                margin-right: 12px;
                min-width: 45px;
                text-align: center;
            ">
                {slot_label}
            </div>
            <div style="flex-grow: 1;">
                <div style="font-weight: bold; font-size: 16px; color: white;">
                    {player['player_name']}
                </div>
                <div style="font-size: 13px; color: white; opacity: 0.8;">
                    {player.get('nfl_team', 'N/A')}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Empty slot placeholder showing position name
        st.markdown(f"""
        <div style="
            border: 2px dashed #666666;
            border-radius: 8px;
            padding: 8px 12px;
            background-color: #2B2B2B;
            margin: 2px 0;
            display: flex;
            align-items: center;
            min-height: 45px;
            color: #CCCCCC;
            font-style: italic;
            width: 100%;
        ">
            <div style="
                background-color: #404040;
                color: #CCCCCC;
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                margin-right: 12px;
                min-width: 45px;
                text-align: center;
            ">
                {slot_label}
            </div>
            <div style="flex-grow: 1; font-size: 14px; color: #CCCCCC;">
                Empty
            </div>
        </div>
        """, unsafe_allow_html=True)


def calculate_roster_height():
    """Calculate the height needed for the roster section based on configuration"""
    if not st.session_state.draft_engine:
        return 400  # Default height
    
    roster_config = st.session_state.draft_engine.roster_config
    
    # Base height for headers and padding
    base_height = 100
    
    # Height per position slot (including labels and player cards)
    slot_height = 65
    
    # Count starting lineup positions
    starting_positions = 0
    for position in ['QB', 'RB', 'WR', 'TE', 'FLEX', 'SUPERFLEX', 'K', 'DEF']:
        starting_positions += roster_config.get(position, 0)
    
    # Count bench positions
    bench_positions = roster_config.get('BENCH', 0)
    
    # Add extra height for section headers (Starting Lineup, Bench)
    section_headers = 60
    
    total_height = base_height + (starting_positions * slot_height) + (bench_positions * slot_height) + section_headers
    
    # Ensure minimum height and reasonable maximum
    return max(400, min(total_height, 800))

def show_available_players(expanded=False):
    """Display available players with dynamic scrolling to match roster height"""
    # Add expanded indicator when in full width mode
    if expanded or not st.session_state.rosters_expanded:
        st.subheader("Available Players")
    else:
        st.subheader("Available Players")
    
    player_db = st.session_state.player_db
    drafted_players = st.session_state.draft_engine.get_drafted_players()
    
    # Initialize filter states
    if 'available_players_position_filter' not in st.session_state:
        st.session_state.available_players_position_filter = "All"
    if 'search_expanded' not in st.session_state:
        st.session_state.search_expanded = False
    
    # Get roster configuration and create position options
    roster_config = st.session_state.draft_engine.roster_config
    position_options = ["All"]
    for position in ['QB', 'RB', 'WR', 'TE', 'FLEX', 'SUPERFLEX', 'K', 'DEF']:
        if roster_config.get(position, 0) > 0:
            position_options.append(position)
    
    # Single line layout with collapsible search
    if st.session_state.search_expanded:
        # Expanded state: search bar takes more space, buttons compressed
        search_col, button_col = st.columns([1.5, 2.5])
        
        with search_col:
            search_term = st.text_input("🔍 Search Player Name", placeholder="Type player name...", key="expanded_search")
            # Auto-collapse when search is empty and loses focus (simulated)
            if not search_term:
                # Add a small collapse button next to search
                if st.button("✕", key="collapse_search", help="Collapse search"):
                    st.session_state.search_expanded = False
                    st.rerun()
    else:
        # Collapsed state: search icon takes minimal space, buttons get more room
        search_col, button_col = st.columns([0.3, 3.7])
        search_term = ""  # No search when collapsed
        
        with search_col:
            # Search icon button to expand
            if st.button("🔍", key="expand_search", help="Click to search players", use_container_width=True):
                st.session_state.search_expanded = True
                st.rerun()
    
    # Position filter buttons - single row layout
    with button_col:
        # Calculate optimal button distribution for single row
        button_cols = st.columns(len(position_options))
        
        for i, position in enumerate(position_options):
            with button_cols[i]:
                button_type = "primary" if st.session_state.available_players_position_filter == position else "secondary"
                # Shorter button labels when search is expanded to save space
                if st.session_state.search_expanded and position not in ["All", "QB", "RB", "WR", "TE", "K"]:
                    # Use shorter labels for longer position names when search is expanded
                    display_label = {"FLEX": "FLX", "SUPERFLEX": "SF", "DEF": "D"}.get(position, position)
                else:
                    display_label = position
                
                if st.button(display_label, key=f"pos_filter_{position}", type=button_type, use_container_width=True):
                    st.session_state.available_players_position_filter = position
                    st.rerun()
    
    # Get filtered players
    position_filter = st.session_state.available_players_position_filter
    
    # Handle special position filters for FLEX and SUPERFLEX
    if position_filter == "FLEX":
        # FLEX positions: RB, WR, TE
        actual_position_filter = ['RB', 'WR', 'TE']
    elif position_filter == "SUPERFLEX":
        # SUPERFLEX positions: QB, RB, WR, TE
        actual_position_filter = ['QB', 'RB', 'WR', 'TE']
    elif position_filter == "All":
        actual_position_filter = None
    else:
        # Regular single position filter
        actual_position_filter = position_filter
    
    available_players = player_db.get_available_players(
        drafted_players=drafted_players,
        search_term=search_term,
        position_filter=actual_position_filter,
        team_filter=None  # Removed team filtering
    )
    
    if available_players.empty:
        st.warning("No players match your current filters.")
        return
    
    # Header row
    header_cols = st.columns([1, 1, 3, 1, 1, 1])
    with header_cols[0]:
        st.write("**Action**")
    with header_cols[1]:
        st.write("**ADP**")
    with header_cols[2]:
        st.write("**Player**")
    with header_cols[3]:
        st.write("**Pos**")
    with header_cols[4]:
        st.write("**Team**")
    with header_cols[5]:
        st.write("**Proj**")

    
    # Calculate height to match roster section
    container_height = calculate_roster_height()
    
    # Add CSS for more compact player rows
    st.markdown("""
    <style>
    /* Decrease row height in available players */
    div[data-testid="column"] {
        padding: 2px 4px !important;
    }

    /* Reduce spacing between player rows */
    .stButton {
        margin: 1px 0 !important;
    }

    /* Reduce text size and line height for more compact display */
    .stMarkdown p {
        font-size: 13px !important;
        line-height: 1.2 !important;
        margin: 2px 0 !important;
    }

    /* Make buttons more compact */
    .stButton button {
        padding: 4px 8px !important;
        font-size: 12px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create scrollable container with dynamic height
    with st.container(height=container_height):
        # Display all players in compact rows
        for idx, player in available_players.iterrows():
            col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 3, 1, 1, 1])
            
            with col1:
                if st.button(f"Draft", key=f"draft_{player['id']}"):
                    draft_player(player)
            
            with col2:
                st.write(f"#{player.get('rank', 'N/A')}")
            
            with col3:
                st.write(f"**{player['name']}**")
            
            with col4:
                st.write(player['position'])
            
            with col5:
                st.write(player['team'])
            
            with col6:
                st.write(player.get('projected_points', 'N/A'))

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
