import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional
import streamlit as st

def export_draft_state(draft_engine) -> str:
    """Export draft state to JSON string"""
    if not draft_engine:
        return json.dumps({})
    
    state_data = draft_engine.export_state()
    state_data['export_timestamp'] = datetime.now().isoformat()
    state_data['app_version'] = "1.0"
    
    return json.dumps(state_data, indent=2)

def import_draft_state(json_string: str):
    """Import draft state from JSON string"""
    try:
        state_data = json.loads(json_string)
        return state_data
    except json.JSONDecodeError:
        return None

def format_pick_number(pick_number: int, league_size: int = 12) -> str:
    """Format pick number as round.pick (e.g., 1.01, 2.12)"""
    if pick_number < 1:
        return "N/A"
    
    round_num = ((pick_number - 1) // league_size) + 1
    pick_in_round = ((pick_number - 1) % league_size) + 1
    
    return f"{round_num}.{pick_in_round:02d}"

def calculate_draft_position_value(position: int, league_size: int, draft_type: str = "snake") -> Dict[str, Any]:
    """Calculate the value and characteristics of a draft position"""
    total_rounds = 15  # Typical fantasy league
    
    if draft_type.lower() == "snake":
        picks = []
        for round_num in range(1, total_rounds + 1):
            if round_num % 2 == 1:  # Odd rounds
                pick_in_round = position
            else:  # Even rounds
                pick_in_round = league_size - position + 1
            
            overall_pick = (round_num - 1) * league_size + pick_in_round
            picks.append(overall_pick)
    else:  # Linear draft
        picks = [position + (round_num - 1) * league_size for round_num in range(1, total_rounds + 1)]
    
    # Calculate average pick position
    avg_pick = sum(picks) / len(picks)
    early_picks = sum(1 for pick in picks[:7] if pick <= league_size * 3)  # First 3 rounds
    
    return {
        'all_picks': picks,
        'average_pick': avg_pick,
        'early_round_picks': early_picks,
        'first_pick': picks[0],
        'second_pick': picks[1] if len(picks) > 1 else None
    }

def get_positional_tier_breaks() -> Dict[str, list]:
    """Define tier breaks for different positions"""
    return {
        'QB': [5, 12, 20, 32],  # Tier breaks at these rankings
        'RB': [8, 16, 24, 35, 50],
        'WR': [10, 20, 35, 50, 70],
        'TE': [3, 8, 15, 25],
        'K': [5, 12],
        'DEF': [5, 12]
    }

def calculate_player_tier(position: str, rank: int) -> int:
    """Calculate which tier a player belongs to based on position and rank"""
    tier_breaks = get_positional_tier_breaks()
    
    if position not in tier_breaks:
        return 1
    
    breaks = tier_breaks[position]
    
    for i, break_point in enumerate(breaks):
        if rank <= break_point:
            return i + 1
    
    return len(breaks) + 1

def format_time_remaining(seconds: int) -> str:
    """Format seconds into MM:SS format for draft timer"""
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"

def calculate_remaining_budget(drafted_players: list, total_budget: int = 200) -> Dict[str, Any]:
    """Calculate remaining auction budget (for auction drafts)"""
    spent = sum(player.get('cost', 0) for player in drafted_players)
    remaining = total_budget - spent
    remaining_players = 15 - len(drafted_players)  # Assuming 15-player rosters
    
    avg_per_remaining = remaining / remaining_players if remaining_players > 0 else 0
    
    return {
        'total_budget': total_budget,
        'spent': spent,
        'remaining': remaining,
        'remaining_players': remaining_players,
        'avg_per_remaining': avg_per_remaining
    }

def get_bye_week_conflicts(roster: list) -> Dict[int, list]:
    """Find bye week conflicts in a roster"""
    bye_weeks = {}
    
    for player in roster:
        bye_week = player.get('bye_week')
        if bye_week:
            if bye_week not in bye_weeks:
                bye_weeks[bye_week] = []
            bye_weeks[bye_week].append(player['player_name'])
    
    # Return only weeks with multiple players
    conflicts = {week: players for week, players in bye_weeks.items() if len(players) > 1}
    return conflicts

def calculate_positional_scarcity_score(position: str, remaining_count: int, total_count: int) -> float:
    """Calculate a scarcity score for a position (0-1, where 1 is most scarce)"""
    if total_count == 0:
        return 0
    
    drafted_percentage = 1 - (remaining_count / total_count)
    
    # Weight by position importance/scarcity
    position_weights = {
        'RB': 1.2,  # RB is typically most scarce
        'WR': 1.0,
        'QB': 0.8,
        'TE': 1.1,
        'K': 0.3,
        'DEF': 0.3
    }
    
    weight = position_weights.get(position, 1.0)
    return min(drafted_percentage * weight, 1.0)

def generate_draft_recap(draft_engine) -> Dict[str, Any]:
    """Generate a comprehensive draft recap"""
    if not draft_engine:
        return {}
    
    user_roster = draft_engine.get_team_roster(draft_engine.user_position)
    all_picks = draft_engine.get_draft_board()
    
    # Calculate draft grades and analytics
    position_counts = {}
    total_projection = 0
    
    for player in user_roster:
        pos = player['position']
        position_counts[pos] = position_counts.get(pos, 0) + 1
        # Add projected points if available
    
    # Find best/worst picks by round
    user_picks = [pick for pick in all_picks if pick['team'] == draft_engine.user_position]
    
    recap = {
        'draft_summary': {
            'total_picks': len(user_picks),
            'positions_drafted': position_counts,
            'draft_grade': 'B+',  # Placeholder - could implement actual grading logic
        },
        'key_picks': {
            'best_value': None,  # Could implement value calculation
            'biggest_reach': None,
            'sleeper_picks': []
        },
        'team_needs': draft_engine.get_position_needs(draft_engine.user_position),
        'bye_week_analysis': get_bye_week_conflicts(user_roster)
    }
    
    return recap

def validate_roster_construction(roster: list, roster_config: Dict[str, int]) -> Dict[str, Any]:
    """Validate if roster meets league requirements"""
    position_counts = {}
    
    for player in roster:
        pos = player['position']
        position_counts[pos] = position_counts.get(pos, 0) + 1
    
    issues = []
    warnings = []
    
    for pos, required in roster_config.items():
        if pos == 'BENCH':
            continue
            
        current = position_counts.get(pos, 0)
        if current < required:
            issues.append(f"Need {required - current} more {pos}")
        elif current > required and pos != 'FLEX':
            warnings.append(f"{current - required} extra {pos} (consider FLEX eligibility)")
    
    return {
        'is_valid': len(issues) == 0,
        'issues': issues,
        'warnings': warnings,
        'position_counts': position_counts
    }

def get_suggested_targets(available_players: pd.DataFrame, team_needs: Dict[str, int], 
                         count: int = 10) -> pd.DataFrame:
    """Get suggested draft targets based on team needs"""
    if available_players.empty:
        return pd.DataFrame()
    
    # Prioritize players at needed positions
    needed_positions = list(team_needs.keys())
    
    if needed_positions:
        priority_players = available_players[
            available_players['position'].isin(needed_positions)
        ].head(count // 2)
        
        other_players = available_players[
            ~available_players['position'].isin(needed_positions)
        ].head(count // 2)
        
        suggestions = pd.concat([priority_players, other_players])
    else:
        suggestions = available_players.head(count)
    
    return suggestions.sort_values('rank')

def export_to_csv(data: list, filename: str) -> str:
    """Export data to CSV format"""
    if not data:
        return ""
    
    df = pd.DataFrame(data)
    return df.to_csv(index=False)

def calculate_strength_of_schedule(player_team: str, week: int = None) -> Dict[str, Any]:
    """Calculate strength of schedule for a player's team (placeholder)"""
    # This would need actual NFL schedule data
    return {
        'overall_difficulty': 'Medium',
        'next_3_weeks': ['Easy', 'Hard', 'Medium'],
        'playoff_schedule': 'Favorable'
    }

@st.cache_data
def load_adp_data() -> pd.DataFrame:
    """Load Average Draft Position data (cached)"""
    # This would load from a real ADP source
    # For now, return empty DataFrame
    return pd.DataFrame()

def compare_to_adp(player_rank: int, player_adp: float) -> Dict[str, Any]:
    """Compare a player's current rank to their ADP"""
    if not player_adp:
        return {'is_value': False, 'difference': 0}
    
    difference = player_adp - player_rank
    is_value = difference > 10  # Drafted 10+ spots later than ADP
    is_reach = difference < -10  # Drafted 10+ spots earlier than ADP
    
    return {
        'is_value': is_value,
        'is_reach': is_reach,
        'difference': difference,
        'value_description': f"{'Value' if is_value else 'Reach' if is_reach else 'Fair'} pick"
    }

def generate_cheat_sheet(available_players: pd.DataFrame, team_needs: Dict[str, int]) -> str:
    """Generate a printable cheat sheet"""
    if available_players.empty:
        return "No players available"
    
    cheat_sheet = "=== FANTASY FOOTBALL CHEAT SHEET ===\n\n"
    
    # Top overall players
    cheat_sheet += "TOP AVAILABLE PLAYERS:\n"
    for _, player in available_players.head(20).iterrows():
        cheat_sheet += f"{player['rank']:3d}. {player['name']:<20} {player['position']:<3} {player['team']}\n"
    
    cheat_sheet += "\n"
    
    # Players by position need
    if team_needs:
        cheat_sheet += "PLAYERS AT NEEDED POSITIONS:\n"
        for pos in team_needs.keys():
            pos_players = available_players[available_players['position'] == pos].head(5)
            if not pos_players.empty:
                cheat_sheet += f"\n{pos}:\n"
                for _, player in pos_players.iterrows():
                    cheat_sheet += f"  {player['name']:<20} {player['team']}\n"
    
    return cheat_sheet
