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
    
    def assign_player_to_pick(self, pick_number: int, player_id: str, player_name: str, 
                             position: str, team: int, nfl_team: str = None) -> bool:
        """Manually assign a player to a specific pick number (for admin use)"""
        # Convert numpy data types to Python native types
        if hasattr(player_id, 'item'):  # numpy types have .item() method
            player_id = str(player_id.item())
        else:
            player_id = str(player_id)
        
        if hasattr(player_name, 'item'):
            player_name = str(player_name.item())
        else:
            player_name = str(player_name)
        
        if hasattr(position, 'item'):
            position = str(position.item())
        else:
            position = str(position)
        
        if nfl_team and hasattr(nfl_team, 'item'):
            nfl_team = str(nfl_team.item())
        elif nfl_team:
            nfl_team = str(nfl_team)
        
        # Validate pick number
        if pick_number < 1 or pick_number > self.total_picks:
            print(f"DEBUG: Invalid pick number {pick_number}, must be 1-{self.total_picks}")
            return False
        
        # Check if pick is already taken
        existing_picks = [p['pick_number'] for p in self.drafted_players]
        if pick_number in existing_picks:
            print(f"DEBUG: Pick {pick_number} already taken. Existing picks: {sorted(existing_picks)}")
            return False
        
        # Validate team number
        if team < 1 or team > self.league_size:
            print(f"DEBUG: Invalid team number {team}, must be 1-{self.league_size}")
            return False
        
        # Validate required parameters
        if not player_id or not player_name or not position:
            print(f"DEBUG: Missing required parameters - ID: {player_id}, Name: {player_name}, Position: {position}")
            return False
        
        # Calculate round number
        round_num = ((pick_number - 1) // self.league_size) + 1
        
        print(f"DEBUG: Creating pick record - Pick: {pick_number}, Round: {round_num}, Team: {team}, Player: {player_name}")
        
        # Create draft pick record
        pick_record = {
            'pick_number': pick_number,
            'round': round_num,
            'team': team,
            'player_id': player_id,
            'player_name': player_name,
            'position': position,
            'nfl_team': nfl_team
        }
        
        # Add to draft record and team roster
        self.drafted_players.append(pick_record)
        self.team_rosters[team].append(pick_record)
        
        # Sort drafted_players by pick_number to maintain order
        self.drafted_players.sort(key=lambda x: x['pick_number'])
        
        print(f"DEBUG: Successfully added pick. Total drafted players: {len(self.drafted_players)}")
        
        # Update current pick to the next available (unpicked) slot
        # Get all picked numbers and sort them
        all_picked_numbers = sorted([p['pick_number'] for p in self.drafted_players])
        
        # Find the first gap in the sequence or the next number after the highest pick
        next_pick = 1
        for pick_num in all_picked_numbers:
            if pick_num == next_pick:
                next_pick += 1
            elif pick_num > next_pick:
                # Found a gap, current next_pick is the correct one
                break
        
        # Ensure we don't exceed total picks
        if next_pick > self.total_picks:
            next_pick = self.total_picks + 1
        
        old_current_pick = self.current_pick
        self.current_pick = next_pick
        
        # Update current round based on the new current pick
        if self.current_pick <= self.total_picks:
            self.current_round = ((self.current_pick - 1) // self.league_size) + 1
        else:
            # Draft is complete
            self.current_round = self.total_rounds + 1
        
        print(f"DEBUG: Updated current pick from {old_current_pick} to {self.current_pick}, round {self.current_round}")
        
        return True
    
    def undo_last_pick(self) -> bool:
        """Undo the last draft pick"""
        if not self.drafted_players:
            return False
        
        last_pick = self.drafted_players.pop()
        team = last_pick['team']
        self.team_rosters[team] = [p for p in self.team_rosters[team] 
                                  if p['pick_number'] != last_pick['pick_number']]
        
        # Update current pick to the next available (unpicked) slot
        # Get all remaining picked numbers and sort them
        all_picked_numbers = sorted([p['pick_number'] for p in self.drafted_players])
        
        # Find the first gap in the sequence or the next number after the highest pick
        next_pick = 1
        for pick_num in all_picked_numbers:
            if pick_num == next_pick:
                next_pick += 1
            elif pick_num > next_pick:
                # Found a gap, current next_pick is the correct one
                break
        
        # Ensure we don't exceed total picks
        if next_pick > self.total_picks:
            next_pick = self.total_picks + 1
        
        self.current_pick = next_pick
        
        # Update current round based on the new current pick
        if self.current_pick <= self.total_picks:
            self.current_round = ((self.current_pick - 1) // self.league_size) + 1
        else:
            # Draft is complete
            self.current_round = self.total_rounds + 1
        
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
