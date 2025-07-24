import pandas as pd
from typing import List, Dict, Optional, Tuple

class DraftEngine:
    """Handles all draft logic, pick order, and state management"""
    
    def __init__(self, league_size: int, user_position: int, scoring_format: str, 
                 draft_type: str, roster_config: Dict[str, int], total_rounds: int):
        self.league_size = league_size
        self.user_position = user_position
        self.scoring_format = scoring_format
        self.draft_type = draft_type.lower()
        self.roster_config = roster_config
        self.total_rounds = total_rounds
        self.total_picks = league_size * total_rounds
        
        # Draft state
        self.current_pick = 1
        self.current_round = 1
        self.drafted_players = []  # List of draft pick objects
        self.team_rosters = {i: [] for i in range(1, league_size + 1)}
        
        # Generate draft order
        self.draft_order = self._generate_draft_order()
    
    def _generate_draft_order(self) -> List[int]:
        """Generate the complete draft order based on draft type"""
        order = []
        
        for round_num in range(1, self.total_rounds + 1):
            if self.draft_type == 'snake' and round_num % 2 == 0:
                # Even rounds go in reverse order for snake draft
                round_order = list(range(self.league_size, 0, -1))
            else:
                # Odd rounds (or all rounds for linear) go in normal order
                round_order = list(range(1, self.league_size + 1))
            
            order.extend(round_order)
        
        return order
    
    def get_current_team(self) -> int:
        """Get the team number for the current pick"""
        if self.current_pick > self.total_picks:
            return None
        return self.draft_order[self.current_pick - 1]
    
    def get_pick_info(self, pick_number: int) -> Dict:
        """Get information about a specific pick number"""
        if pick_number < 1 or pick_number > self.total_picks:
            return None
        
        team = self.draft_order[pick_number - 1]
        round_num = ((pick_number - 1) // self.league_size) + 1
        
        return {
            'pick_number': pick_number,
            'team': team,
            'round': round_num,
            'is_user_pick': team == self.user_position
        }
    
    def get_next_user_picks(self, count: int = 5) -> List[int]:
        """Get the next few pick numbers for the user"""
        user_picks = []
        
        for pick_num in range(self.current_pick, min(self.current_pick + 50, self.total_picks + 1)):
            if self.draft_order[pick_num - 1] == self.user_position:
                user_picks.append(pick_num)
                if len(user_picks) >= count:
                    break
        
        return user_picks
    
    def draft_player(self, player_id: str, player_name: str, position: str, 
                    team: int, nfl_team: str = None) -> bool:
        """Draft a player to a team"""
        if self.current_pick > self.total_picks:
            return False
        
        # Verify it's the correct team's turn
        if team != self.get_current_team():
            return False
        
        # Create draft pick record
        pick_record = {
            'pick_number': self.current_pick,
            'round': self.current_round,
            'team': team,
            'player_id': player_id,
            'player_name': player_name,
            'position': position,
            'nfl_team': nfl_team
        }
        
        # Add to draft record and team roster
        self.drafted_players.append(pick_record)
        self.team_rosters[team].append(pick_record)
        
        # Advance to next pick
        self.current_pick += 1
        if (self.current_pick - 1) % self.league_size == 0:
            self.current_round += 1
        
        return True
    
    def undo_last_pick(self) -> bool:
        """Undo the last draft pick"""
        if not self.drafted_players:
            return False
        
        last_pick = self.drafted_players.pop()
        team = last_pick['team']
        self.team_rosters[team] = [p for p in self.team_rosters[team] 
                                  if p['pick_number'] != last_pick['pick_number']]
        
        self.current_pick -= 1
        self.current_round = ((self.current_pick - 1) // self.league_size) + 1
        
        return True
    
    def get_draft_board(self) -> List[Dict]:
        """Get the current draft board"""
        return self.drafted_players.copy()
    
    def get_drafted_players(self) -> List[str]:
        """Get list of drafted player IDs"""
        return [pick['player_id'] for pick in self.drafted_players]
    
    def get_team_roster(self, team_number: int) -> List[Dict]:
        """Get the roster for a specific team"""
        return self.team_rosters.get(team_number, []).copy()
    
    def is_draft_complete(self) -> bool:
        """Check if the draft is complete"""
        return self.current_pick > self.total_picks
    
    def get_draft_status(self) -> Dict:
        """Get overall draft status"""
        return {
            'current_pick': self.current_pick,
            'current_round': self.current_round,
            'total_picks': self.total_picks,
            'total_rounds': self.total_rounds,
            'picks_remaining': self.total_picks - self.current_pick + 1,
            'is_complete': self.is_draft_complete(),
            'current_team': self.get_current_team()
        }
    
    def get_position_needs(self, team_number: int) -> Dict[str, int]:
        """Calculate position needs for a team"""
        roster = self.get_team_roster(team_number)
        position_counts = {}
        
        for player in roster:
            pos = player['position']
            position_counts[pos] = position_counts.get(pos, 0) + 1
        
        needs = {}
        for pos, required in self.roster_config.items():
            if pos == 'BENCH':
                continue
            current = position_counts.get(pos, 0)
            if current < required:
                needs[pos] = required - current
        
        return needs
    
    def simulate_to_user_pick(self) -> Optional[int]:
        """Simulate the draft to the next user pick (for AI opponents)"""
        # This could be extended to include AI logic for other teams
        next_user_picks = self.get_next_user_picks(1)
        return next_user_picks[0] if next_user_picks else None
    
    def export_state(self) -> Dict:
        """Export the current draft state"""
        return {
            'league_size': self.league_size,
            'user_position': self.user_position,
            'scoring_format': self.scoring_format,
            'draft_type': self.draft_type,
            'roster_config': self.roster_config,
            'total_rounds': self.total_rounds,
            'current_pick': self.current_pick,
            'current_round': self.current_round,
            'drafted_players': self.drafted_players,
            'team_rosters': self.team_rosters
        }
    
    def import_state(self, state_data: Dict) -> bool:
        """Import a draft state"""
        try:
            self.league_size = state_data['league_size']
            self.user_position = state_data['user_position']
            self.scoring_format = state_data['scoring_format']
            self.draft_type = state_data['draft_type']
            self.roster_config = state_data['roster_config']
            self.total_rounds = state_data['total_rounds']
            self.current_pick = state_data['current_pick']
            self.current_round = state_data['current_round']
            self.drafted_players = state_data['drafted_players']
            self.team_rosters = state_data['team_rosters']
            
            # Regenerate dependent values
            self.total_picks = self.league_size * self.total_rounds
            self.draft_order = self._generate_draft_order()
            
            return True
        except KeyError:
            return False
