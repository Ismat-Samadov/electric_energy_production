#!/usr/bin/env python3
"""
Chess Game Analysis Script
Analyzes PGN file and generates insights for skill improvement
"""

import re
from collections import defaultdict, Counter
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

class ChessAnalyzer:
    def __init__(self, pgn_file):
        self.pgn_file = pgn_file
        self.games = []
        self.stats = {
            'total_games': 0,
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'white_games': 0,
            'black_games': 0,
            'white_wins': 0,
            'black_wins': 0,
            'openings': defaultdict(lambda: {'wins': 0, 'losses': 0, 'draws': 0, 'total': 0}),
            'eco_codes': defaultdict(lambda: {'wins': 0, 'losses': 0, 'draws': 0, 'total': 0}),
            'rating_history': [],
            'opponents_rating': [],
            'terminations': Counter(),
            'time_controls': Counter(),
            'moves_count': [],
            'rating_diffs': [],
            'blunders': [],
            'mistakes': [],
            'inaccuracies': []
        }

    def parse_pgn(self):
        """Parse PGN file and extract game data"""
        print("Parsing PGN file...")

        with open(self.pgn_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split into individual games
        game_blocks = content.split('\n\n\n')

        for block in game_blocks:
            if not block.strip():
                continue

            game_data = {}
            lines = block.split('\n')

            # Parse headers
            for line in lines:
                if line.startswith('['):
                    match = re.match(r'\[(\w+)\s+"([^"]+)"\]', line)
                    if match:
                        key, value = match.groups()
                        game_data[key] = value
                elif line.strip() and not line.startswith('['):
                    # This is the moves line
                    game_data['moves'] = line

            if game_data:
                self.games.append(game_data)

        print(f"Parsed {len(self.games)} games")

    def analyze_games(self):
        """Analyze all games and collect statistics"""
        print("Analyzing games...")

        for game in self.games:
            self.stats['total_games'] += 1

            # Determine color
            is_white = game.get('White') == 'IsmatS'
            if is_white:
                self.stats['white_games'] += 1
            else:
                self.stats['black_games'] += 1

            # Result analysis
            result = game.get('Result', '')
            won = (result == '1-0' and is_white) or (result == '0-1' and not is_white)
            lost = (result == '0-1' and is_white) or (result == '1-0' and not is_white)
            draw = result == '1/2-1/2'

            if won:
                self.stats['wins'] += 1
                if is_white:
                    self.stats['white_wins'] += 1
                else:
                    self.stats['black_wins'] += 1
            elif lost:
                self.stats['losses'] += 1
            elif draw:
                self.stats['draws'] += 1

            # Opening analysis
            opening = game.get('Opening', 'Unknown')
            eco = game.get('ECO', 'Unknown')

            if won:
                self.stats['openings'][opening]['wins'] += 1
                self.stats['eco_codes'][eco]['wins'] += 1
            elif lost:
                self.stats['openings'][opening]['losses'] += 1
                self.stats['eco_codes'][eco]['losses'] += 1
            else:
                self.stats['openings'][opening]['draws'] += 1
                self.stats['eco_codes'][eco]['draws'] += 1

            self.stats['openings'][opening]['total'] += 1
            self.stats['eco_codes'][eco]['total'] += 1

            # Rating tracking
            try:
                if is_white:
                    my_elo_str = game.get('WhiteElo', '0')
                    opp_elo_str = game.get('BlackElo', '0')
                    rating_diff = game.get('WhiteRatingDiff', '0')
                else:
                    my_elo_str = game.get('BlackElo', '0')
                    opp_elo_str = game.get('WhiteElo', '0')
                    rating_diff = game.get('BlackRatingDiff', '0')

                # Skip games with missing ratings
                if my_elo_str == '?' or opp_elo_str == '?':
                    continue

                my_elo = int(my_elo_str)
                opp_elo = int(opp_elo_str)

                self.stats['rating_history'].append(my_elo)
                self.stats['opponents_rating'].append(opp_elo)

                try:
                    self.stats['rating_diffs'].append(int(rating_diff))
                except:
                    pass
            except ValueError:
                # Skip games with invalid rating data
                pass

            # Termination
            termination = game.get('Termination', 'Unknown')
            self.stats['terminations'][termination] += 1

            # Time control
            time_control = game.get('TimeControl', 'Unknown')
            self.stats['time_controls'][time_control] += 1

            # Analyze moves for blunders/mistakes
            moves = game.get('moves', '')
            self.analyze_moves_quality(moves, won, lost)

    def analyze_moves_quality(self, moves_text, won, lost):
        """Analyze move quality (blunders, mistakes, inaccuracies)"""
        blunders = len(re.findall(r'\?\?', moves_text))
        mistakes = len(re.findall(r'\?(?!\?)', moves_text))
        inaccuracies = len(re.findall(r'\?!', moves_text))

        # Count moves
        move_count = len(re.findall(r'\d+\.', moves_text))

        self.stats['blunders'].append(blunders)
        self.stats['mistakes'].append(mistakes)
        self.stats['inaccuracies'].append(inaccuracies)
        self.stats['moves_count'].append(move_count)

    def generate_visualizations(self):
        """Generate all visualization charts"""
        print("Generating visualizations...")

        charts_dir = 'charts'
        os.makedirs(charts_dir, exist_ok=True)

        # 1. Win/Loss/Draw Distribution
        self.plot_results_distribution(charts_dir)

        # 2. Performance by Color
        self.plot_color_performance(charts_dir)

        # 3. Rating Progress
        self.plot_rating_progress(charts_dir)

        # 4. Top Openings Performance
        self.plot_openings_performance(charts_dir)

        # 5. Mistakes Analysis
        self.plot_mistakes_analysis(charts_dir)

        # 6. Opponent Rating Distribution
        self.plot_opponent_rating_distribution(charts_dir)

        # 7. Win Rate vs Opponent Rating
        self.plot_winrate_vs_rating(charts_dir)

        print(f"All charts saved to {charts_dir}/")

    def plot_results_distribution(self, charts_dir):
        """Plot win/loss/draw pie chart"""
        fig, ax = plt.subplots(figsize=(10, 8))

        sizes = [self.stats['wins'], self.stats['losses'], self.stats['draws']]
        labels = ['Wins', 'Losses', 'Draws']
        colors = ['#2ecc71', '#e74c3c', '#95a5a6']
        explode = (0.1, 0, 0)

        ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
               shadow=True, startangle=90, textprops={'fontsize': 14, 'weight': 'bold'})
        ax.set_title('Overall Game Results', fontsize=18, weight='bold', pad=20)

        # Add statistics text
        total = sum(sizes)
        win_rate = (self.stats['wins'] / total * 100) if total > 0 else 0
        plt.figtext(0.5, 0.02, f'Total Games: {total} | Win Rate: {win_rate:.1f}%',
                    ha='center', fontsize=12, style='italic')

        plt.tight_layout()
        plt.savefig(f'{charts_dir}/01_results_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()

    def plot_color_performance(self, charts_dir):
        """Plot performance as White vs Black"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        # White performance
        white_losses = self.stats['white_games'] - self.stats['white_wins']
        white_data = [self.stats['white_wins'], white_losses]
        white_labels = ['Wins', 'Losses']
        white_colors = ['#2ecc71', '#e74c3c']

        ax1.pie(white_data, labels=white_labels, colors=white_colors, autopct='%1.1f%%',
                shadow=True, startangle=90, textprops={'fontsize': 12, 'weight': 'bold'})
        white_wr = (self.stats['white_wins'] / self.stats['white_games'] * 100) if self.stats['white_games'] > 0 else 0
        ax1.set_title(f'Performance as White\n({self.stats["white_games"]} games | WR: {white_wr:.1f}%)',
                     fontsize=16, weight='bold', pad=15)

        # Black performance
        black_losses = self.stats['black_games'] - self.stats['black_wins']
        black_data = [self.stats['black_wins'], black_losses]
        black_labels = ['Wins', 'Losses']
        black_colors = ['#2ecc71', '#e74c3c']

        ax2.pie(black_data, labels=black_labels, colors=black_colors, autopct='%1.1f%%',
                shadow=True, startangle=90, textprops={'fontsize': 12, 'weight': 'bold'})
        black_wr = (self.stats['black_wins'] / self.stats['black_games'] * 100) if self.stats['black_games'] > 0 else 0
        ax2.set_title(f'Performance as Black\n({self.stats["black_games"]} games | WR: {black_wr:.1f}%)',
                     fontsize=16, weight='bold', pad=15)

        plt.tight_layout()
        plt.savefig(f'{charts_dir}/02_color_performance.png', dpi=300, bbox_inches='tight')
        plt.close()

    def plot_rating_progress(self, charts_dir):
        """Plot rating progression over time"""
        fig, ax = plt.subplots(figsize=(14, 8))

        games = list(range(1, len(self.stats['rating_history']) + 1))
        ratings = self.stats['rating_history']

        ax.plot(games, ratings, linewidth=2, color='#3498db', marker='o', markersize=4, alpha=0.7)
        ax.fill_between(games, ratings, alpha=0.3, color='#3498db')

        # Add trend line
        if len(games) > 1:
            z = np.polyfit(games, ratings, 1)
            p = np.poly1d(z)
            ax.plot(games, p(games), "--", color='#e74c3c', linewidth=2, alpha=0.8, label='Trend')

        ax.set_xlabel('Game Number', fontsize=14, weight='bold')
        ax.set_ylabel('Rating', fontsize=14, weight='bold')
        ax.set_title('Rating Progress Over Time', fontsize=18, weight='bold', pad=20)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=12)

        # Add stats as subtitle
        if ratings:
            start_rating = ratings[0]
            end_rating = ratings[-1]
            change = end_rating - start_rating
            peak_rating = max(ratings)

            stats_text = f'Start: {start_rating} | Current: {end_rating} | Change: {change:+d} | Peak: {peak_rating}'

            # Add text box at bottom of plot area
            ax.text(0.5, -0.12, stats_text,
                   transform=ax.transAxes,
                   ha='center', va='top',
                   fontsize=12, style='italic',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='wheat', alpha=0.3))

        plt.tight_layout()
        plt.savefig(f'{charts_dir}/03_rating_progress.png', dpi=300, bbox_inches='tight')
        plt.close()

    def plot_openings_performance(self, charts_dir):
        """Plot top openings by frequency and win rate"""
        # Get top 10 most played openings
        top_openings = sorted(self.stats['openings'].items(),
                            key=lambda x: x[1]['total'], reverse=True)[:10]

        if not top_openings:
            return

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))

        # Chart 1: Games played per opening
        openings = [name[:40] for name, _ in top_openings]
        totals = [data['total'] for _, data in top_openings]

        bars1 = ax1.barh(openings, totals, color='#3498db', alpha=0.7)
        ax1.set_xlabel('Games Played', fontsize=12, weight='bold')
        ax1.set_title('Top 10 Most Played Openings', fontsize=16, weight='bold', pad=15)
        ax1.invert_yaxis()

        # Add value labels
        for i, bar in enumerate(bars1):
            width = bar.get_width()
            ax1.text(width, bar.get_y() + bar.get_height()/2, f' {int(width)}',
                    ha='left', va='center', fontsize=10, weight='bold')

        # Chart 2: Win rate per opening
        win_rates = []
        for name, data in top_openings:
            wr = (data['wins'] / data['total'] * 100) if data['total'] > 0 else 0
            win_rates.append(wr)

        colors = ['#2ecc71' if wr >= 50 else '#e74c3c' for wr in win_rates]
        bars2 = ax2.barh(openings, win_rates, color=colors, alpha=0.7)
        ax2.set_xlabel('Win Rate (%)', fontsize=12, weight='bold')
        ax2.set_title('Win Rate by Opening', fontsize=16, weight='bold', pad=15)
        ax2.axvline(x=50, color='black', linestyle='--', linewidth=1, alpha=0.5)
        ax2.invert_yaxis()

        # Add value labels
        for i, bar in enumerate(bars2):
            width = bar.get_width()
            ax2.text(width, bar.get_y() + bar.get_height()/2, f' {width:.1f}%',
                    ha='left', va='center', fontsize=10, weight='bold')

        plt.tight_layout()
        plt.savefig(f'{charts_dir}/04_openings_performance.png', dpi=300, bbox_inches='tight')
        plt.close()

    def plot_mistakes_analysis(self, charts_dir):
        """Plot mistakes, blunders, and inaccuracies analysis"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

        # Average mistakes per game
        avg_blunders = sum(self.stats['blunders']) / len(self.stats['blunders']) if self.stats['blunders'] else 0
        avg_mistakes = sum(self.stats['mistakes']) / len(self.stats['mistakes']) if self.stats['mistakes'] else 0
        avg_inaccuracies = sum(self.stats['inaccuracies']) / len(self.stats['inaccuracies']) if self.stats['inaccuracies'] else 0

        categories = ['Blunders\n(??)', 'Mistakes\n(?)', 'Inaccuracies\n(?!)']
        values = [avg_blunders, avg_mistakes, avg_inaccuracies]
        colors_bar = ['#e74c3c', '#f39c12', '#f1c40f']

        bars = ax1.bar(categories, values, color=colors_bar, alpha=0.7, edgecolor='black', linewidth=2)
        ax1.set_ylabel('Average per Game', fontsize=12, weight='bold')
        ax1.set_title('Average Move Quality Issues', fontsize=14, weight='bold', pad=15)
        ax1.grid(True, alpha=0.3, axis='y')

        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}', ha='center', va='bottom', fontsize=11, weight='bold')

        # Blunders distribution
        if self.stats['blunders']:
            ax2.hist(self.stats['blunders'], bins=range(0, max(self.stats['blunders'])+2),
                    color='#e74c3c', alpha=0.7, edgecolor='black')
            ax2.set_xlabel('Blunders per Game', fontsize=11, weight='bold')
            ax2.set_ylabel('Frequency', fontsize=11, weight='bold')
            ax2.set_title('Blunders Distribution', fontsize=14, weight='bold', pad=10)
            ax2.grid(True, alpha=0.3, axis='y')

        # Mistakes over time
        if self.stats['mistakes']:
            games_range = range(1, len(self.stats['mistakes']) + 1)
            ax3.plot(games_range, self.stats['mistakes'], color='#f39c12',
                    marker='o', markersize=3, alpha=0.6, linewidth=1.5)
            ax3.set_xlabel('Game Number', fontsize=11, weight='bold')
            ax3.set_ylabel('Mistakes', fontsize=11, weight='bold')
            ax3.set_title('Mistakes Over Time', fontsize=14, weight='bold', pad=10)
            ax3.grid(True, alpha=0.3)

            # Add trend line
            if len(games_range) > 1:
                z = np.polyfit(list(games_range), self.stats['mistakes'], 1)
                p = np.poly1d(z)
                ax3.plot(games_range, p(games_range), "--", color='red', linewidth=2, alpha=0.7, label='Trend')
                ax3.legend()

        # Game length distribution
        if self.stats['moves_count']:
            ax4.hist(self.stats['moves_count'], bins=20, color='#9b59b6', alpha=0.7, edgecolor='black')
            ax4.set_xlabel('Number of Moves', fontsize=11, weight='bold')
            ax4.set_ylabel('Frequency', fontsize=11, weight='bold')
            ax4.set_title('Game Length Distribution', fontsize=14, weight='bold', pad=10)
            ax4.grid(True, alpha=0.3, axis='y')

            avg_moves = sum(self.stats['moves_count']) / len(self.stats['moves_count'])
            ax4.axvline(avg_moves, color='red', linestyle='--', linewidth=2, label=f'Average: {avg_moves:.1f}')
            ax4.legend()

        plt.tight_layout()
        plt.savefig(f'{charts_dir}/05_mistakes_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()

    def plot_opponent_rating_distribution(self, charts_dir):
        """Plot distribution of opponent ratings"""
        fig, ax = plt.subplots(figsize=(12, 7))

        if self.stats['opponents_rating']:
            ax.hist(self.stats['opponents_rating'], bins=20, color='#e67e22',
                   alpha=0.7, edgecolor='black', linewidth=1.5)
            ax.set_xlabel('Opponent Rating', fontsize=13, weight='bold')
            ax.set_ylabel('Frequency', fontsize=13, weight='bold')
            ax.set_title('Opponent Rating Distribution', fontsize=16, weight='bold', pad=15)
            ax.grid(True, alpha=0.3, axis='y')

            avg_opp = sum(self.stats['opponents_rating']) / len(self.stats['opponents_rating'])
            ax.axvline(avg_opp, color='red', linestyle='--', linewidth=2,
                      label=f'Average: {avg_opp:.0f}')
            ax.legend(fontsize=12)

        plt.tight_layout()
        plt.savefig(f'{charts_dir}/06_opponent_rating_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()

    def plot_winrate_vs_rating(self, charts_dir):
        """Plot win rate against opponent rating difference"""
        fig, ax = plt.subplots(figsize=(12, 7))

        # Calculate rating differences and results
        rating_buckets = defaultdict(lambda: {'wins': 0, 'total': 0})

        for i, game in enumerate(self.games):
            is_white = game.get('White') == 'IsmatS'
            result = game.get('Result', '')

            try:
                if is_white:
                    my_elo_str = game.get('WhiteElo', '0')
                    opp_elo_str = game.get('BlackElo', '0')
                else:
                    my_elo_str = game.get('BlackElo', '0')
                    opp_elo_str = game.get('WhiteElo', '0')

                # Skip games with missing ratings
                if my_elo_str == '?' or opp_elo_str == '?':
                    continue

                my_elo = int(my_elo_str)
                opp_elo = int(opp_elo_str)

                diff = my_elo - opp_elo
                bucket = (diff // 50) * 50  # Group by 50 rating points

                won = (result == '1-0' and is_white) or (result == '0-1' and not is_white)

                rating_buckets[bucket]['total'] += 1
                if won:
                    rating_buckets[bucket]['wins'] += 1
            except (ValueError, TypeError):
                # Skip games with invalid rating data
                continue

        # Sort and plot
        sorted_buckets = sorted(rating_buckets.items())
        if sorted_buckets:
            x_vals = [bucket for bucket, _ in sorted_buckets]
            y_vals = [(data['wins']/data['total']*100) if data['total'] > 0 else 0
                     for _, data in sorted_buckets]
            sizes = [data['total']*20 for _, data in sorted_buckets]

            scatter = ax.scatter(x_vals, y_vals, s=sizes, alpha=0.6, c=y_vals,
                               cmap='RdYlGn', edgecolors='black', linewidth=1.5)
            ax.axhline(y=50, color='black', linestyle='--', linewidth=1, alpha=0.5, label='50% Win Rate')
            ax.axvline(x=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)

            ax.set_xlabel('Rating Difference (You - Opponent)', fontsize=13, weight='bold')
            ax.set_ylabel('Win Rate (%)', fontsize=13, weight='bold')
            ax.set_title('Win Rate vs Opponent Rating Difference', fontsize=16, weight='bold', pad=15)
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=11)

            # Add colorbar
            cbar = plt.colorbar(scatter, ax=ax)
            cbar.set_label('Win Rate (%)', fontsize=11, weight='bold')

        plt.tight_layout()
        plt.savefig(f'{charts_dir}/07_winrate_vs_rating_diff.png', dpi=300, bbox_inches='tight')
        plt.close()

    def generate_insights(self):
        """Generate actionable insights for improvement"""
        insights = []

        # Overall performance
        total = self.stats['total_games']
        win_rate = (self.stats['wins'] / total * 100) if total > 0 else 0

        insights.append("## 📊 Overall Performance")
        insights.append(f"- **Total Games**: {total}")
        insights.append(f"- **Win Rate**: {win_rate:.1f}%")
        insights.append(f"- **Wins**: {self.stats['wins']} | **Losses**: {self.stats['losses']} | **Draws**: {self.stats['draws']}")
        insights.append("")

        # Color performance
        white_wr = (self.stats['white_wins'] / self.stats['white_games'] * 100) if self.stats['white_games'] > 0 else 0
        black_wr = (self.stats['black_wins'] / self.stats['black_games'] * 100) if self.stats['black_games'] > 0 else 0

        insights.append("## ⚫⚪ Color Performance")
        insights.append(f"- **As White**: {white_wr:.1f}% win rate ({self.stats['white_wins']}/{self.stats['white_games']} games)")
        insights.append(f"- **As Black**: {black_wr:.1f}% win rate ({self.stats['black_wins']}/{self.stats['black_games']} games)")

        if white_wr > black_wr + 10:
            insights.append(f"- ⚠️ **INSIGHT**: You perform {white_wr - black_wr:.1f}% better as White. Focus on improving Black repertoire.")
        elif black_wr > white_wr + 10:
            insights.append(f"- ⚠️ **INSIGHT**: You perform {black_wr - white_wr:.1f}% better as Black. Review White opening preparation.")
        else:
            insights.append("- ✅ **INSIGHT**: Balanced performance with both colors.")
        insights.append("")

        # Rating progress
        if self.stats['rating_history']:
            start_rating = self.stats['rating_history'][0]
            end_rating = self.stats['rating_history'][-1]
            peak_rating = max(self.stats['rating_history'])
            change = end_rating - start_rating

            insights.append("## 📈 Rating Progress")
            insights.append(f"- **Starting Rating**: {start_rating}")
            insights.append(f"- **Current Rating**: {end_rating}")
            insights.append(f"- **Peak Rating**: {peak_rating}")
            insights.append(f"- **Change**: {change:+d} points")

            if change > 0:
                insights.append(f"- ✅ **INSIGHT**: Positive rating trend! Keep up the good work.")
            else:
                insights.append(f"- ⚠️ **INSIGHT**: Rating declined. Review recent losses and focus on consistency.")
            insights.append("")

        # Opening performance
        insights.append("## 📖 Opening Performance")

        # Best openings
        opening_winrates = []
        for opening, data in self.stats['openings'].items():
            if data['total'] >= 3:  # At least 3 games
                wr = (data['wins'] / data['total'] * 100)
                opening_winrates.append((opening, wr, data['total']))

        if opening_winrates:
            best_openings = sorted(opening_winrates, key=lambda x: x[1], reverse=True)[:3]
            worst_openings = sorted(opening_winrates, key=lambda x: x[1])[:3]

            insights.append("**Best Openings (3+ games)**:")
            for opening, wr, games in best_openings:
                insights.append(f"- {opening}: {wr:.1f}% ({games} games)")

            insights.append("\n**Weakest Openings (3+ games)**:")
            for opening, wr, games in worst_openings:
                insights.append(f"- {opening}: {wr:.1f}% ({games} games)")

            insights.append(f"\n- ⚠️ **INSIGHT**: Avoid '{worst_openings[0][0]}' (your weakest opening) or study it more deeply.")
            insights.append(f"- ✅ **INSIGHT**: '{best_openings[0][0]}' is your strongest opening. Play it more often!")
        insights.append("")

        # Mistakes analysis
        if self.stats['blunders']:
            avg_blunders = sum(self.stats['blunders']) / len(self.stats['blunders'])
            avg_mistakes = sum(self.stats['mistakes']) / len(self.stats['mistakes'])
            avg_inaccuracies = sum(self.stats['inaccuracies']) / len(self.stats['inaccuracies'])

            insights.append("## 🎯 Move Quality Analysis")
            insights.append(f"- **Average Blunders per game**: {avg_blunders:.2f}")
            insights.append(f"- **Average Mistakes per game**: {avg_mistakes:.2f}")
            insights.append(f"- **Average Inaccuracies per game**: {avg_inaccuracies:.2f}")

            if avg_blunders > 1.5:
                insights.append("- ⚠️ **CRITICAL**: Too many blunders! Slow down and double-check moves before playing.")
            elif avg_blunders > 0.8:
                insights.append("- ⚠️ **INSIGHT**: Work on reducing blunders through tactics training and careful play.")
            else:
                insights.append("- ✅ **INSIGHT**: Good blunder rate. Keep maintaining focus.")
            insights.append("")

        # Game length
        if self.stats['moves_count']:
            avg_moves = sum(self.stats['moves_count']) / len(self.stats['moves_count'])
            insights.append("## ⏱️ Game Characteristics")
            insights.append(f"- **Average Game Length**: {avg_moves:.1f} moves")

            if avg_moves < 30:
                insights.append("- ⚠️ **INSIGHT**: Games end quickly. Focus on surviving the opening and early middlegame.")
            elif avg_moves > 50:
                insights.append("- ⚠️ **INSIGHT**: Games go long. Study endgame techniques to convert advantages.")
            insights.append("")

        # Key recommendations
        insights.append("## 🎓 Key Recommendations")
        insights.append("")
        insights.append("### 1. Tactical Training")
        insights.append("- Practice daily tactics puzzles (20-30 minutes)")
        insights.append("- Focus on pattern recognition")
        insights.append("- Use tactics trainers like Chess.com puzzles or Lichess puzzles")
        insights.append("")

        insights.append("### 2. Opening Preparation")
        if worst_openings:
            insights.append(f"- Study the theory of '{worst_openings[0][0]}' or replace it with a better alternative")
        insights.append("- Learn at least 10-15 moves deep in your main openings")
        insights.append("- Focus on understanding ideas rather than memorizing moves")
        insights.append("")

        insights.append("### 3. Reduce Mistakes")
        insights.append("- Implement a pre-move checklist:")
        insights.append("  - Check for opponent threats")
        insights.append("  - Look for hanging pieces")
        insights.append("  - Calculate forcing moves (checks, captures, threats)")
        insights.append("  - Consider opponent's best response")
        insights.append("")

        insights.append("### 4. Time Management")
        insights.append("- Use your time wisely in critical positions")
        insights.append("- Don't rush in the opening")
        insights.append("- Save time for complex middlegame and endgame positions")
        insights.append("")

        insights.append("### 5. Post-Game Analysis")
        insights.append("- Review every game you play, especially losses")
        insights.append("- Identify your mistakes and understand why they happened")
        insights.append("- Look for missed tactical opportunities")
        insights.append("- Use computer analysis to find better moves")
        insights.append("")

        insights.append("### 6. Study Plan")
        insights.append("- **Daily**: 30 min tactics + review 1 game")
        insights.append("- **Weekly**: Study 1 opening variation deeply")
        insights.append("- **Monthly**: Work through instructive master games in your openings")
        insights.append("")

        return "\n".join(insights)

    def print_summary(self):
        """Print analysis summary"""
        print("\n" + "="*60)
        print("CHESS ANALYSIS SUMMARY")
        print("="*60)
        print(f"\nTotal Games Analyzed: {self.stats['total_games']}")
        print(f"Win Rate: {(self.stats['wins']/self.stats['total_games']*100):.1f}%")
        print(f"White Win Rate: {(self.stats['white_wins']/self.stats['white_games']*100):.1f}%")
        print(f"Black Win Rate: {(self.stats['black_wins']/self.stats['black_games']*100):.1f}%")

        if self.stats['rating_history']:
            print(f"\nRating Change: {self.stats['rating_history'][-1] - self.stats['rating_history'][0]:+d}")
            print(f"Peak Rating: {max(self.stats['rating_history'])}")

        print("\nMost Played Openings:")
        top_5 = sorted(self.stats['openings'].items(), key=lambda x: x[1]['total'], reverse=True)[:5]
        for opening, data in top_5:
            wr = (data['wins'] / data['total'] * 100) if data['total'] > 0 else 0
            print(f"  - {opening[:50]}: {data['total']} games ({wr:.1f}% WR)")

        print("\n" + "="*60 + "\n")


def main():
    pgn_file = '/Users/ismatsamadov/IsmatS/lichess_IsmatS_2025-11-29.pgn'

    # Create analyzer
    analyzer = ChessAnalyzer(pgn_file)

    # Parse and analyze
    analyzer.parse_pgn()
    analyzer.analyze_games()

    # Print summary
    analyzer.print_summary()

    # Generate visualizations
    analyzer.generate_visualizations()

    # Generate insights
    insights = analyzer.generate_insights()

    # Save insights to file
    with open('chess_insights.md', 'w') as f:
        f.write("# Chess Performance Analysis & Improvement Insights\n\n")
        f.write(insights)

    print("✅ Analysis complete!")
    print("📊 Charts saved to charts/ directory")
    print("📝 Insights saved to chess_insights.md")


if __name__ == '__main__':
    main()
