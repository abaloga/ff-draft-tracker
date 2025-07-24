# Fantasy Football Draft Assistant 🏈

A Python Streamlit application designed to help you dominate your fantasy football draft with real-time tracking, player analytics, and strategic insights.

## Features

### 🚀 Core Functionality
- **Live Draft Tracking**: Real-time draft board with all picks and remaining players
- **Smart Configuration**: Support for 8-16 team leagues with customizable roster settings
- **Draft Types**: Both Snake and Linear draft formats supported
- **Scoring Formats**: PPR, Half-PPR, and Standard scoring options

### 📊 Draft Management
- **Player Database**: Comprehensive player rankings with projections
- **Position Tracking**: Monitor roster construction and identify needs
- **Pick Calculator**: Always know when your next pick is coming
- **User Alerts**: Visual notifications when it's your turn to draft

### 🎯 Strategic Tools
- **Available Players**: Searchable and filterable player lists
- **Team Analysis**: Track all team rosters and strategy
- **Draft Summary**: Post-draft analytics and team grades
- **Export/Import**: Save and share draft states

## Installation

1. Install Python 3.8 or higher
2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:
```bash
streamlit run app.py
```

2. Open your browser to the provided URL (typically http://localhost:8501)

3. Configure your draft settings:
   - Number of teams (8-16)
   - Your draft position
   - Scoring format (PPR/Half-PPR/Standard)
   - Draft type (Snake/Linear)
   - Roster configuration

4. Start drafting! The app will:
   - Track all picks in real-time
   - Alert you when it's your turn
   - Show available players with search/filter options
   - Provide team analysis and recommendations

## Project Structure

```
ff draft tracker/
├── app.py              # Main Streamlit application
├── draft_logic.py      # Draft order and pick calculations
├── player_data.py      # Player database and rankings
├── utils.py           # Helper functions and utilities
├── requirements.txt   # Python dependencies
└── README.md         # This file
```

## Draft Configuration Options

### League Settings
- **Teams**: 8-16 teams supported
- **Draft Position**: Your slot in the draft order
- **Scoring**: PPR, Half-PPR, or Standard
- **Draft Type**: Snake (reversing) or Linear (same order)

### Roster Composition
- **QB**: Quarterback positions (1-3)
- **RB**: Running Back positions (1-4)  
- **WR**: Wide Receiver positions (1-4)
- **TE**: Tight End positions (1-3)
- **FLEX**: Flexible RB/WR/TE positions (0-3)
- **K**: Kicker positions (0-2)
- **DEF**: Defense positions (0-2)
- **Bench**: Bench positions (4-10)

## Key Features Explained

### Snake Draft Logic
- Round 1: Teams 1-12 (in order)
- Round 2: Teams 12-1 (reverse order)
- Round 3: Teams 1-12 (back to normal order)
- And so on...

### Player Database
The app includes a comprehensive player database with:
- 300+ fantasy-relevant players
- Position rankings and tiers
- Projected fantasy points
- NFL team affiliations
- Bye week information

### Draft Board
- Visual representation of all completed picks
- Organized by round and team
- Color-coded for easy reading
- Your picks highlighted

### Available Players
- Real-time list of undrafted players
- Search by player name
- Filter by position or NFL team
- Sort by rankings or projections
- One-click drafting

## Tips for Live Drafts

1. **Pre-Draft Setup**: Configure your league settings before the draft starts
2. **Stay Alert**: The app will notify you when it's your turn, but stay engaged
3. **Use Filters**: Narrow down player lists by position when you have specific needs
4. **Track Opponents**: Monitor other teams' roster construction for strategic advantages
5. **Export Data**: Save your draft results for future reference

## Advanced Features

### Team Analysis
- Roster composition tracking
- Position need identification
- Bye week conflict detection
- Strength analysis

### Draft Analytics
- Pick value assessment
- Positional scarcity tracking
- Draft grade calculations
- Historical comparisons

## Contributing

This is a personal project, but suggestions and improvements are welcome! Feel free to:
- Report bugs or issues
- Suggest new features
- Contribute player data updates
- Improve the user interface

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

Player rankings and projections are for entertainment purposes only. Fantasy football involves skill and luck - draft at your own risk! 🎲

---

**Good luck with your draft!** 🏆
