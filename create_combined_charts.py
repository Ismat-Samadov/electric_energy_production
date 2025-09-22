import chess.pgn
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

plt.style.use('default')
sns.set_palette("husl")

def parse_pgn_file(filename):
    """Parse a PGN file and extract game data"""
    games = []

    with open(filename, 'r', encoding='utf-8') as f:
        while True:
            try:
                game = chess.pgn.read_game(f)
                if game is None:
                    break

                headers = game.headers
                account = None
                if 'White' in headers and 'Black' in headers:
                    if headers['White'] in ['IsmatS', 'Cassiny']:
                        account = headers['White']
                    elif headers['Black'] in ['IsmatS', 'Cassiny']:
                        account = headers['Black']

                result = headers.get('Result', '')
                if account:
                    def safe_int(value, default=0):
                        try:
                            return int(value)
                        except (ValueError, TypeError):
                            return default

                    if account == headers.get('White'):
                        player_result = 'win' if result == '1-0' else 'loss' if result == '0-1' else 'draw'
                        player_color = 'white'
                        player_elo = safe_int(headers.get('WhiteElo', 0))
                        opponent_elo = safe_int(headers.get('BlackElo', 0))
                        rating_diff = safe_int(headers.get('WhiteRatingDiff', 0))
                    else:
                        player_result = 'win' if result == '0-1' else 'loss' if result == '1-0' else 'draw'
                        player_color = 'black'
                        player_elo = safe_int(headers.get('BlackElo', 0))
                        opponent_elo = safe_int(headers.get('WhiteElo', 0))
                        rating_diff = safe_int(headers.get('BlackRatingDiff', 0))
                else:
                    continue

                time_control = headers.get('TimeControl', '')
                if '+' in time_control:
                    base_time, increment = map(int, time_control.split('+'))
                else:
                    base_time = int(time_control) if time_control.isdigit() else 0
                    increment = 0

                total_time = base_time + increment * 40
                if total_time < 180:
                    game_type = 'bullet'
                elif total_time < 600:
                    game_type = 'blitz'
                elif total_time < 1800:
                    game_type = 'rapid'
                else:
                    game_type = 'classical'

                moves = []
                board = game.board()
                for move in game.mainline_moves():
                    moves.append(move)
                    board.push(move)

                game_data = {
                    'account': account,
                    'date': headers.get('Date', ''),
                    'utc_date': headers.get('UTCDate', ''),
                    'utc_time': headers.get('UTCTime', ''),
                    'result': player_result,
                    'color': player_color,
                    'player_elo': player_elo,
                    'opponent_elo': opponent_elo,
                    'elo_diff': opponent_elo - player_elo,
                    'rating_change': rating_diff,
                    'opening': headers.get('Opening', ''),
                    'eco_code': headers.get('ECO', ''),
                    'termination': headers.get('Termination', ''),
                    'time_control': time_control,
                    'game_type': game_type,
                    'base_time': base_time,
                    'increment': increment,
                    'total_moves': len(moves),
                    'site': headers.get('Site', ''),
                    'event': headers.get('Event', '')
                }
                games.append(game_data)

            except Exception as e:
                continue

    return games

def analyze_combined_data(df):
    """Analyze as combined dataset"""
    df['datetime'] = pd.to_datetime(df['utc_date'] + ' ' + df['utc_time'])
    df['hour'] = df['datetime'].dt.hour
    df['day_of_week'] = df['datetime'].dt.day_name()
    df['month'] = df['datetime'].dt.month
    df['year'] = df['datetime'].dt.year

    def get_time_period(hour):
        if 5 <= hour < 9: return 'Early Morning'
        elif 9 <= hour < 12: return 'Late Morning'
        elif 12 <= hour < 14: return 'Lunch Time'
        elif 14 <= hour < 17: return 'Afternoon'
        elif 17 <= hour < 20: return 'Evening'
        elif 20 <= hour < 23: return 'Night'
        else: return 'Late Night'

    def get_season(month):
        if month in [12, 1, 2]: return 'Winter'
        elif month in [3, 4, 5]: return 'Spring'
        elif month in [6, 7, 8]: return 'Summer'
        else: return 'Autumn'

    df['time_period'] = df['hour'].apply(get_time_period)
    df['season'] = df['month'].apply(get_season)
    df['weekend_weekday'] = df['day_of_week'].apply(lambda x: 'Weekend' if x in ['Saturday', 'Sunday'] else 'Weekday')

    return df

def create_combined_charts(df):
    """Create combined analysis charts"""

    plt.rcParams['figure.facecolor'] = 'white'
    plt.rcParams['axes.facecolor'] = 'white'

    # Chart 1: Your Overall Win Rate Over Time
    plt.figure(figsize=(14, 8))
    df_sorted = df.sort_values('datetime')
    df_sorted['game_number'] = range(len(df_sorted))
    df_sorted['result_numeric'] = (df_sorted['result'] == 'win').astype(int)
    df_sorted['rolling_winrate'] = df_sorted['result_numeric'].rolling(window=100, min_periods=10).mean() * 100

    plt.plot(df_sorted['game_number'], df_sorted['rolling_winrate'], linewidth=2, color='#2ecc71')
    plt.axhline(y=50, color='red', linestyle='--', alpha=0.7, label='50% Baseline')
    plt.title('Your Chess Performance Evolution (100-game rolling average)', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Game Number', fontsize=12)
    plt.ylabel('Win Rate (%)', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend()

    # Add account phase annotations
    ismats_games = len(df[df['account'] == 'IsmatS'])
    cassiny_games = len(df[df['account'] == 'Cassiny'])

    plt.axvline(x=ismats_games, color='orange', linestyle=':', alpha=0.7,
                label=f'Account Mix (IsmatS: {ismats_games}, Cassiny: {cassiny_games})')
    plt.legend()
    plt.tight_layout()
    plt.savefig('assets/combined_01_performance_evolution.png', dpi=300, bbox_inches='tight')
    plt.close()

    # Chart 2: Your Performance by Time of Day
    plt.figure(figsize=(14, 8))
    hourly_performance = df.groupby('hour').agg({
        'result': [lambda x: (x == 'win').mean() * 100, 'count']
    }).round(1)
    hourly_performance.columns = ['win_rate', 'game_count']

    # Filter hours with at least 20 games
    hourly_performance = hourly_performance[hourly_performance['game_count'] >= 20]

    plt.plot(hourly_performance.index, hourly_performance['win_rate'],
             marker='o', linewidth=3, markersize=8, color='#9b59b6')

    # Highlight peak hours
    peak_hour = hourly_performance['win_rate'].idxmax()
    worst_hour = hourly_performance['win_rate'].idxmin()

    plt.scatter(peak_hour, hourly_performance.loc[peak_hour, 'win_rate'],
                color='gold', s=200, zorder=5, label=f'Peak: {peak_hour}:00')
    plt.scatter(worst_hour, hourly_performance.loc[worst_hour, 'win_rate'],
                color='red', s=200, zorder=5, label=f'Worst: {worst_hour}:00')

    plt.title('Your Circadian Performance Pattern', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Hour of Day', fontsize=12)
    plt.ylabel('Win Rate (%)', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.xticks(range(0, 24, 2))
    plt.tight_layout()
    plt.savefig('assets/combined_02_circadian_pattern.png', dpi=300, bbox_inches='tight')
    plt.close()

    # Chart 3: Your Game Results Distribution
    plt.figure(figsize=(10, 8))
    result_counts = df['result'].value_counts()
    colors = ['#2ecc71', '#e74c3c', '#f39c12']

    plt.pie(result_counts.values, labels=result_counts.index, autopct='%1.1f%%',
            colors=colors, startangle=90, textprops={'fontsize': 12})
    plt.title('Your Overall Game Results Distribution\n(10,961 Total Games)',
              fontsize=16, fontweight='bold', pad=20)

    # Add statistics text
    win_rate = (df['result'] == 'win').mean() * 100
    plt.text(0, -1.3, f'Overall Win Rate: {win_rate:.1f}%',
             ha='center', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('assets/combined_03_results_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()

    # Chart 4: Your Performance by Game Type
    plt.figure(figsize=(12, 8))
    game_type_stats = df.groupby('game_type').agg({
        'result': [lambda x: (x == 'win').mean() * 100, 'count']
    }).round(1)
    game_type_stats.columns = ['win_rate', 'game_count']

    x_pos = range(len(game_type_stats))
    bars = plt.bar(x_pos, game_type_stats['win_rate'], color=['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4'])

    # Add game count labels on bars
    for i, (idx, row) in enumerate(game_type_stats.iterrows()):
        plt.text(i, row['win_rate'] + 1, f"{int(row['game_count'])} games",
                ha='center', va='bottom', fontweight='bold')
        plt.text(i, row['win_rate']/2, f"{row['win_rate']:.1f}%",
                ha='center', va='center', fontweight='bold', color='white', fontsize=12)

    plt.title('Your Performance Across Different Time Controls', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Game Type', fontsize=12)
    plt.ylabel('Win Rate (%)', fontsize=12)
    plt.xticks(x_pos, game_type_stats.index)
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig('assets/combined_04_game_types.png', dpi=300, bbox_inches='tight')
    plt.close()

    # Chart 5: Your Seasonal Performance
    plt.figure(figsize=(12, 8))
    seasonal_stats = df.groupby('season').agg({
        'result': [lambda x: (x == 'win').mean() * 100, 'count']
    }).round(1)
    seasonal_stats.columns = ['win_rate', 'game_count']

    x_pos = range(len(seasonal_stats))
    bars = plt.bar(x_pos, seasonal_stats['win_rate'],
                   color=['#3498db', '#e74c3c', '#f39c12', '#2ecc71'])

    for i, (idx, row) in enumerate(seasonal_stats.iterrows()):
        plt.text(i, row['win_rate'] + 1, f"{int(row['game_count'])} games",
                ha='center', va='bottom', fontweight='bold')
        plt.text(i, row['win_rate']/2, f"{row['win_rate']:.1f}%",
                ha='center', va='center', fontweight='bold', color='white', fontsize=12)

    plt.title('Your Seasonal Performance Patterns', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Season', fontsize=12)
    plt.ylabel('Win Rate (%)', fontsize=12)
    plt.xticks(x_pos, seasonal_stats.index)
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig('assets/combined_05_seasonal_patterns.png', dpi=300, bbox_inches='tight')
    plt.close()

    # Chart 6: Your Opening Performance (Top 10)
    plt.figure(figsize=(14, 10))
    opening_stats = df.groupby('opening').agg({
        'result': [lambda x: (x == 'win').mean() * 100, 'count']
    }).round(1)
    opening_stats.columns = ['win_rate', 'game_count']

    # Get top 10 most played openings
    top_openings = opening_stats.nlargest(10, 'game_count')

    y_pos = range(len(top_openings))
    bars = plt.barh(y_pos, top_openings['game_count'], color='#1abc9c')

    # Add win rate labels
    for i, (idx, row) in enumerate(top_openings.iterrows()):
        plt.text(row['game_count'] + 20, i, f"{row['win_rate']:.1f}% WR",
                va='center', fontweight='bold')

    plt.yticks(y_pos, [opening[:50] + '...' if len(opening) > 50 else opening
                       for opening in top_openings.index])
    plt.title('Your Top 10 Most Played Openings', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Number of Games', fontsize=12)
    plt.gca().invert_yaxis()
    plt.grid(True, alpha=0.3, axis='x')
    plt.tight_layout()
    plt.savefig('assets/combined_06_top_openings.png', dpi=300, bbox_inches='tight')
    plt.close()

    # Chart 7: Your Rating Journey Combined
    plt.figure(figsize=(16, 8))

    # Combine both accounts chronologically
    df_sorted = df.sort_values('datetime')
    df_sorted['cumulative_rating'] = df_sorted.groupby('account')['rating_change'].cumsum()

    # Add initial ratings
    df_sorted.loc[df_sorted['account'] == 'IsmatS', 'cumulative_rating'] += 1500
    df_sorted.loc[df_sorted['account'] == 'Cassiny', 'cumulative_rating'] += 1598

    # Plot combined rating evolution
    ismats_data = df_sorted[df_sorted['account'] == 'IsmatS']
    cassiny_data = df_sorted[df_sorted['account'] == 'Cassiny']

    if len(ismats_data) > 0:
        plt.plot(ismats_data['datetime'], ismats_data['cumulative_rating'],
                linewidth=2, alpha=0.8, label='Focused Play Mode (IsmatS)', color='#e74c3c')

    if len(cassiny_data) > 0:
        plt.plot(cassiny_data['datetime'], cassiny_data['cumulative_rating'],
                linewidth=2, alpha=0.8, label='Volume Play Mode (Cassiny)', color='#3498db')

    plt.title('Your Complete Rating Journey Across Both Accounts', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Rating', fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('assets/combined_07_rating_journey.png', dpi=300, bbox_inches='tight')
    plt.close()

    # Chart 8: Your Time Period Performance
    plt.figure(figsize=(12, 8))
    time_period_stats = df.groupby('time_period').agg({
        'result': [lambda x: (x == 'win').mean() * 100, 'count']
    }).round(1)
    time_period_stats.columns = ['win_rate', 'game_count']

    # Reorder by logical time progression
    time_order = ['Early Morning', 'Late Morning', 'Lunch Time', 'Afternoon', 'Evening', 'Night', 'Late Night']
    time_period_stats = time_period_stats.reindex([t for t in time_order if t in time_period_stats.index])

    x_pos = range(len(time_period_stats))
    bars = plt.bar(x_pos, time_period_stats['win_rate'],
                   color=['#ff6b6b', '#feca57', '#48dbfb', '#ff9ff3', '#54a0ff', '#5f27cd', '#00d2d3'])

    for i, (idx, row) in enumerate(time_period_stats.iterrows()):
        plt.text(i, row['win_rate'] + 1, f"{int(row['game_count'])}",
                ha='center', va='bottom', fontweight='bold', fontsize=10)
        plt.text(i, row['win_rate']/2, f"{row['win_rate']:.1f}%",
                ha='center', va='center', fontweight='bold', color='white', fontsize=11)

    plt.title('Your Performance by Time Period', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Time Period', fontsize=12)
    plt.ylabel('Win Rate (%)', fontsize=12)
    plt.xticks(x_pos, time_period_stats.index, rotation=45)
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig('assets/combined_08_time_periods.png', dpi=300, bbox_inches='tight')
    plt.close()

def main():
    print("Creating combined analysis charts...")

    # Parse both PGN files
    print("Parsing IsmatS.pgn...")
    ismats_games = parse_pgn_file('IsmatS.pgn')

    print("Parsing Cassiny.pgn...")
    cassiny_games = parse_pgn_file('Cassiny.pgn')

    # Combine data
    all_games = ismats_games + cassiny_games
    df = pd.DataFrame(all_games)

    # Analyze combined data
    df = analyze_combined_data(df)

    # Create combined charts
    print("Creating combined analysis charts...")
    create_combined_charts(df)

    print("\nCombined analysis charts created successfully!")
    print("Generated 8 charts analyzing your complete chess journey!")

if __name__ == "__main__":
    main()