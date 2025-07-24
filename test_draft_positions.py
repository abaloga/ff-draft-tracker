#!/usr/bin/env python3
"""
Test script to verify draft position functionality works with different team counts
"""

import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from draft_logic import DraftEngine

def test_draft_positions():
    """Test draft logic with different team counts and user positions"""
    
    test_cases = [
        (8, 1), (8, 4), (8, 8),   # 8-team league
        (10, 1), (10, 5), (10, 10), # 10-team league  
        (12, 1), (12, 6), (12, 12), # 12-team league
        (14, 1), (14, 7), (14, 14), # 14-team league
    ]
    
    for league_size, user_position in test_cases:
        print(f"\n=== Testing {league_size}-team league, user position {user_position} ===")
        
        # Create draft engine
        roster_config = {
            'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1, 'FLEX': 1, 
            'SUPERFLEX': 0, 'K': 1, 'DEF': 1, 'BENCH': 6
        }
        
        engine = DraftEngine(
            league_size=league_size,
            user_position=user_position,
            scoring_format="PPR",
            draft_type="snake",
            roster_config=roster_config,
            total_rounds=15
        )
        
        # Test basic properties
        print(f"League size: {engine.league_size}")
        print(f"User position: {engine.user_position}")
        print(f"Total picks: {engine.total_picks}")
        print(f"Current team: {engine.get_current_team()}")
        
        # Test draft order (first round)
        first_round = engine.draft_order[:league_size]
        print(f"First round order: {first_round}")
        
        # Test snake draft (second round if applicable)
        if engine.total_rounds > 1:
            second_round = engine.draft_order[league_size:league_size*2]
            print(f"Second round order: {second_round}")
        
        # Test user's next picks
        user_picks = engine.get_next_user_picks(3)
        print(f"User's next 3 picks: {user_picks}")
        
        # Validate that user position is correct
        user_pick_teams = [engine.draft_order[pick-1] for pick in user_picks]
        all_correct = all(team == user_position for team in user_pick_teams)
        print(f"User picks validation: {'✓ PASS' if all_correct else '✗ FAIL'}")
        
        # Test pick info
        if user_picks:
            first_user_pick = user_picks[0]
            pick_info = engine.get_pick_info(first_user_pick)
            print(f"First user pick info: {pick_info}")

if __name__ == "__main__":
    test_draft_positions()
