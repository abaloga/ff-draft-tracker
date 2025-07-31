import pandas as pd
import json
from typing import List, Dict, Optional, Union
import requests
from pathlib import Path

class PlayerDatabase:
    """Manages fantasy football player data and rankings"""
    
    def __init__(self, data_file: str = None):
        self.data_file = data_file
        self.players_df = pd.DataFrame()
        self.nfl_teams = []
        self.load_player_data()
    
    def load_player_data(self):
        """Load player data from file or generate sample data"""
        if self.data_file and Path(self.data_file).exists():
            try:
                self.players_df = pd.read_csv(self.data_file)
                self.nfl_teams = sorted(self.players_df['team'].unique().tolist())
                return
            except Exception as e:
                print(f"Error loading player data: {e}")
        
        # Generate sample player data if no file exists
        self.players_df = self._generate_sample_data()
        self.nfl_teams = sorted(self.players_df['team'].unique().tolist())
    
    def _generate_sample_data(self) -> pd.DataFrame:
        """Generate sample fantasy football player data"""
        sample_data = []
        
        # Sample QBs
        qbs = [
            ("Josh Allen", "BUF", 1, 285),
            ("Lamar Jackson", "BAL", 2, 275),
            ("Dak Prescott", "DAL", 3, 265),
            ("Joe Burrow", "CIN", 4, 260),
            ("Tua Tagovailoa", "MIA", 5, 250),
            ("Jalen Hurts", "PHI", 6, 245),
            ("Justin Herbert", "LAC", 7, 240),
            ("Kirk Cousins", "ATL", 8, 235),
            ("Brock Purdy", "SF", 9, 230),
            ("Anthony Richardson", "IND", 10, 225),
            ("Caleb Williams", "CHI", 11, 220),
            ("Aaron Rodgers", "NYJ", 12, 215),
            ("Jayden Daniels", "WAS", 13, 210),
            ("Russell Wilson", "PIT", 14, 205),
            ("Geno Smith", "SEA", 15, 200),
        ]
        
        for i, (name, team, rank, points) in enumerate(qbs):
            sample_data.append({
                'id': f'qb_{i+1}',
                'name': name,
                'position': 'QB',
                'team': team,
                'rank': rank,
                'projected_points': points,
                'bye_week': 4 + (i % 14)
            })
        
        # Sample RBs
        rbs = [
            ("Christian McCaffrey", "SF", 1, 320),
            ("Saquon Barkley", "PHI", 2, 295),
            ("Breece Hall", "NYJ", 3, 275),
            ("Bijan Robinson", "ATL", 4, 270),
            ("Derrick Henry", "BAL", 5, 265),
            ("Jonathan Taylor", "IND", 6, 260),
            ("Josh Jacobs", "GB", 7, 255),
            ("De'Von Achane", "MIA", 8, 250),
            ("Kyren Williams", "LAR", 9, 245),
            ("Jahmyr Gibbs", "DET", 10, 240),
            ("Alvin Kamara", "NO", 11, 235),
            ("Kenneth Walker III", "SEA", 12, 230),
            ("Rachaad White", "TB", 13, 225),
            ("Joe Mixon", "HOU", 14, 220),
            ("James Cook", "BUF", 15, 215),
            ("David Montgomery", "DET", 16, 210),
            ("Rhamondre Stevenson", "NE", 17, 205),
            ("Isiah Pacheco", "KC", 18, 200),
            ("Tony Pollard", "TEN", 19, 195),
            ("Najee Harris", "PIT", 20, 190),
        ]
        
        for i, (name, team, rank, points) in enumerate(rbs):
            sample_data.append({
                'id': f'rb_{i+1}',
                'name': name,
                'position': 'RB',
                'team': team,
                'rank': rank + 15,  # Offset for overall ranking
                'projected_points': points,
                'bye_week': 4 + (i % 14)
            })
        
        # Sample WRs
        wrs = [
            ("CeeDee Lamb", "DAL", 1, 285),
            ("Tyreek Hill", "MIA", 2, 280),
            ("Ja'Marr Chase", "CIN", 3, 275),
            ("Justin Jefferson", "MIN", 4, 270),
            ("Amon-Ra St. Brown", "DET", 5, 265),
            ("A.J. Brown", "PHI", 6, 260),
            ("Puka Nacua", "LAR", 7, 255),
            ("Jaylen Waddle", "MIA", 8, 250),
            ("DK Metcalf", "SEA", 9, 245),
            ("DeVonta Smith", "PHI", 10, 240),
            ("Stefon Diggs", "HOU", 11, 235),
            ("Mike Evans", "TB", 12, 230),
            ("Davante Adams", "LV", 13, 225),
            ("DJ Moore", "CHI", 14, 220),
            ("Chris Olave", "NO", 15, 215),
            ("Garrett Wilson", "NYJ", 16, 210),
            ("Tee Higgins", "CIN", 17, 205),
            ("Brandon Aiyuk", "SF", 18, 200),
            ("Cooper Kupp", "LAR", 19, 195),
            ("Keenan Allen", "CHI", 20, 190),
        ]
        
        for i, (name, team, rank, points) in enumerate(wrs):
            sample_data.append({
                'id': f'wr_{i+1}',
                'name': name,
                'position': 'WR',
                'team': team,
                'rank': rank + 35,  # Offset for overall ranking
                'projected_points': points,
                'bye_week': 4 + (i % 14)
            })
        
        # Sample TEs
        tes = [
            ("Travis Kelce", "KC", 1, 185),
            ("Sam LaPorta", "DET", 2, 165),
            ("Mark Andrews", "BAL", 3, 155),
            ("Trey McBride", "ARI", 4, 145),
            ("George Kittle", "SF", 5, 140),
            ("Evan Engram", "JAX", 6, 135),
            ("Kyle Pitts", "ATL", 7, 130),
            ("Dallas Goedert", "PHI", 8, 125),
            ("Jake Ferguson", "DAL", 9, 120),
            ("David Njoku", "CLE", 10, 115),
            ("T.J. Hockenson", "MIN", 11, 110),
            ("Brock Bowers", "LV", 12, 105),
        ]
        
        for i, (name, team, rank, points) in enumerate(tes):
            sample_data.append({
                'id': f'te_{i+1}',
                'name': name,
                'position': 'TE',
                'team': team,
                'rank': rank + 55,  # Offset for overall ranking
                'projected_points': points,
                'bye_week': 4 + (i % 14)
            })
        
        # Sample Kickers
        kickers = [
            ("Justin Tucker", "BAL", 1, 135),
            ("Harrison Butker", "KC", 2, 130),
            ("Tyler Bass", "BUF", 3, 125),
            ("Brandon McManus", "GB", 4, 120),
            ("Jake Elliott", "PHI", 5, 115),
            ("Chris Boswell", "PIT", 6, 110),
            ("Daniel Carlson", "LV", 7, 105),
            ("Younghoe Koo", "ATL", 8, 100),
        ]
        
        for i, (name, team, rank, points) in enumerate(kickers):
            sample_data.append({
                'id': f'k_{i+1}',
                'name': name,
                'position': 'K',
                'team': team,
                'rank': rank + 200,  # Offset for overall ranking
                'projected_points': points,
                'bye_week': 4 + (i % 14)
            })
        
        # Sample Defenses
        defenses = [
            ("San Francisco", "SF", 1, 125),
            ("Dallas", "DAL", 2, 120),
            ("Buffalo", "BUF", 3, 115),
            ("Pittsburgh", "PIT", 4, 110),
            ("Miami", "MIA", 5, 105),
            ("Cleveland", "CLE", 6, 100),
            ("Baltimore", "BAL", 7, 95),
            ("New York Jets", "NYJ", 8, 90),
        ]
        
        for i, (name, team, rank, points) in enumerate(defenses):
            sample_data.append({
                'id': f'def_{i+1}',
                'name': f"{name} Defense",
                'position': 'DEF',
                'team': team,
                'rank': rank + 220,  # Offset for overall ranking
                'projected_points': points,
                'bye_week': 4 + (i % 14)
            })
        
        return pd.DataFrame(sample_data)
    
    def get_available_players(self, drafted_players: List[str], 
                            search_term: str = None, 
                            position_filter: Union[str, List[str]] = None,
                            team_filter: str = None) -> pd.DataFrame:
        """Get available (undrafted) players with optional filters"""
        # Start with all players
        available = self.players_df[~self.players_df['id'].isin(drafted_players)].copy()
        
        # Apply filters
        if search_term:
            available = available[available['name'].str.contains(search_term, case=False, na=False)]
        
        if position_filter:
            if isinstance(position_filter, list):
                # For FLEX/SUPERFLEX - use isin() for multiple positions
                available = available[available['position'].isin(position_filter)]
            else:
                # For single positions - use == as before
                available = available[available['position'] == position_filter]
        
        if team_filter:
            available = available[available['team'] == team_filter]
        
        # Sort by rank
        available = available.sort_values('rank')
        
        return available
    
    def get_player_by_id(self, player_id: str) -> Optional[Dict]:
        """Get a specific player by ID"""
        player = self.players_df[self.players_df['id'] == player_id]
        if player.empty:
            return None
        return player.iloc[0].to_dict()
    
    def get_players_by_position(self, position: str) -> pd.DataFrame:
        """Get all players at a specific position"""
        return self.players_df[self.players_df['position'] == position].sort_values('rank')
    
    def get_top_players(self, position: str = None, count: int = 50) -> pd.DataFrame:
        """Get top players overall or by position"""
        if position:
            players = self.get_players_by_position(position)
        else:
            players = self.players_df.copy()
        
        return players.head(count)
    
    def get_nfl_teams(self) -> List[str]:
        """Get list of all NFL teams"""
        return self.nfl_teams.copy()
    
    def search_players(self, search_term: str, max_results: int = 20) -> pd.DataFrame:
        """Search for players by name"""
        matches = self.players_df[
            self.players_df['name'].str.contains(search_term, case=False, na=False)
        ].sort_values('rank')
        
        return matches.head(max_results)
    
    def get_player_stats(self, player_id: str) -> Optional[Dict]:
        """Get detailed stats for a player (placeholder for future expansion)"""
        player = self.get_player_by_id(player_id)
        if not player:
            return None
        
        # This could be expanded to include more detailed stats
        return {
            'basic_info': player,
            'season_stats': {},  # Placeholder
            'matchup_info': {},  # Placeholder
            'injury_status': 'Healthy'  # Placeholder
        }
    
    def export_rankings(self, filename: str):
        """Export current rankings to CSV"""
        self.players_df.to_csv(filename, index=False)
    
    def import_rankings(self, filename: str) -> bool:
        """Import rankings from CSV file"""
        try:
            self.players_df = pd.read_csv(filename)
            self.nfl_teams = sorted(self.players_df['team'].unique().tolist())
            return True
        except Exception as e:
            print(f"Error importing rankings: {e}")
            return False
    
    def update_player_projection(self, player_id: str, new_projection: float):
        """Update a player's projected points"""
        idx = self.players_df[self.players_df['id'] == player_id].index
        if not idx.empty:
            self.players_df.loc[idx[0], 'projected_points'] = new_projection
    
    def get_positional_scarcity(self, drafted_players: List[str]) -> Dict[str, Dict]:
        """Analyze positional scarcity based on remaining players"""
        available = self.get_available_players(drafted_players)
        scarcity = {}
        
        for position in ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']:
            pos_players = available[available['position'] == position]
            if not pos_players.empty:
                scarcity[position] = {
                    'remaining': len(pos_players),
                    'top_remaining': pos_players.head(10)['name'].tolist(),
                    'avg_projection': pos_players['projected_points'].mean(),
                    'best_available': pos_players.iloc[0]['name'] if len(pos_players) > 0 else None
                }
            else:
                scarcity[position] = {
                    'remaining': 0,
                    'top_remaining': [],
                    'avg_projection': 0,
                    'best_available': None
                }
        
        return scarcity
