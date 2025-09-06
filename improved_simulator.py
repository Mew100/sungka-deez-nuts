# fixed_simulator.py
from main import SungkaGame
from more_balanced_heuristic import SungkaHeuristic
from game_logger import GameLogger
import time
import random
import pandas as pd
import os

class RandomBot:
    def __init__(self, player_index):
        self.player_index = player_index
    
    def get_move(self, game):
        valid_moves = game.get_valid_moves(self.player_index)
        return random.choice(valid_moves) if valid_moves else None

class MaxPolicyBot:
    """Always chooses the house with the most stones"""
    def __init__(self, player_index):
        self.player_index = player_index
    
    def get_move(self, game):
        valid_moves = game.get_valid_moves(self.player_index)
        if not valid_moves:
            return None
        
        # Find the move with the most stones
        return max(valid_moves, key=lambda move: game.board[move])

class ExactPolicyBot:
    """Chooses house where stones equal distance to head for extra turn"""
    def __init__(self, player_index):
        self.player_index = player_index
    
    def get_move(self, game):
        valid_moves = game.get_valid_moves(self.player_index)
        if not valid_moves:
            return None
        
        head_position = 7 if self.player_index == 0 else 15
        exact_moves = []
        
        for move in valid_moves:
            stones = game.board[move]
            # Calculate distance to head, accounting for skipped holes
            distance_to_head = self._calculate_distance_to_head(game, move, head_position)
            
            if stones == distance_to_head:
                exact_moves.append(move)
        
        if exact_moves:
            # Pick the one nearest to head (highest index for P1, lowest for P2)
            if self.player_index == 0:
                return max(exact_moves)  # Nearest to head for P1
            else:
                return min(exact_moves)  # Nearest to head for P2
        
        # Fallback to Max Policy
        return max(valid_moves, key=lambda move: game.board[move])
    
    def _calculate_distance_to_head(self, game, start_hole, head_position):
        """Calculate actual distance considering skipped holes"""
        current_hole = start_hole
        distance = 0
        
        while True:
            current_hole = (current_hole + 1) % 16
            
            # Skip opponent's head
            if (self.player_index == 0 and current_hole == 15) or \
               (self.player_index == 1 and current_hole == 7):
                continue
                
            # Skip burned holes
            if (current_hole in game.burned_holes[0] or 
                current_hole in game.burned_holes[1]):
                continue
            
            distance += 1
            
            if current_hole == head_position:
                break
                
            # Prevent infinite loop
            if distance > 20:
                break
        
        return distance

class RealisticBasicRuleBot:
    """Bot that uses actual basic Sungka strategy"""
    def __init__(self, player_index):
        self.player_index = player_index
    
    def get_move(self, game):
        valid_moves = game.get_valid_moves(self.player_index)
        if not valid_moves:
            return None
        
        # Priority 1: Look for immediate captures
        for move in valid_moves:
            if self.can_capture(game, move):
                return move
        
        # Priority 2: Look for extra turns (land in own head)
        extra_turn_moves = []
        for move in valid_moves:
            if self.gives_extra_turn(game, move):
                extra_turn_moves.append(move)
        
        if extra_turn_moves:
            # Pick the extra turn move with fewest stones (most efficient)
            return min(extra_turn_moves, key=lambda x: game.board[x])
        
        # Priority 3: Pick a reasonable move (moderate stones, middle holes preferred)
        scored_moves = []
        for move in valid_moves:
            score = 0
            stones = game.board[move]
            
            # Prefer moderate stone counts (4-8 stones)
            if 4 <= stones <= 8:
                score += 10
            elif stones <= 2:
                score -= 5
            elif stones >= 12:
                score -= 8
            
            # Prefer middle holes
            if self.player_index == 0:  # Player 1
                if move in [2, 3, 4]:
                    score += 5
                elif move in [0, 6]:
                    score -= 3
            else:  # Player 2
                if move in [10, 11, 12]:
                    score += 5
                elif move in [8, 14]:
                    score -= 3
            
            scored_moves.append((move, score))
        
        return max(scored_moves, key=lambda x: x[1])[0]
    
    def can_capture(self, game, hole):
        """Check if this move leads to a capture"""
        stones = game.board[hole]
        current_hole = hole
        
        # Simple simulation
        while stones > 0:
            current_hole = (current_hole + 1) % 16
            
            # Skip opponent's head
            if (self.player_index == 0 and current_hole == 15) or \
               (self.player_index == 1 and current_hole == 7):
                continue
                
            # Skip burned holes
            if (current_hole in game.burned_holes[0] or 
                current_hole in game.burned_holes[1]):
                continue
                
            stones -= 1
        
        # Check if we land in our own empty hole with stones in opposite
        if ((self.player_index == 0 and 0 <= current_hole <= 6) or
            (self.player_index == 1 and 8 <= current_hole <= 14)):
            if game.board[current_hole] == 0:
                opposite = 14 - current_hole
                return game.board[opposite] > 0
        
        return False
    
    def gives_extra_turn(self, game, hole):
        """Check if this move gives an extra turn"""
        stones = game.board[hole]
        current_hole = hole
        
        while stones > 0:
            current_hole = (current_hole + 1) % 16
            
            # Skip opponent's head
            if (self.player_index == 0 and current_hole == 15) or \
               (self.player_index == 1 and current_hole == 7):
                continue
                
            # Skip burned holes
            if (current_hole in game.burned_holes[0] or 
                current_hole in game.burned_holes[1]):
                continue
                
            stones -= 1
        
        # Check if we land in our own head
        return ((self.player_index == 0 and current_hole == 7) or
                (self.player_index == 1 and current_hole == 15))

class BasicRuleBot:
    def __init__(self, player_index):
        self.player_index = player_index
        self.realistic_bot = RealisticBasicRuleBot(player_index)
    
    def get_move(self, game):
        return self.realistic_bot.get_move(game)

class HeuristicBot:
    def __init__(self, player_index):
        self.player_index = player_index
    
    def get_move(self, game):
        # ✅ FIXED: Create fresh heuristic instance for current game state
        # and temporarily set the current player to this bot's player index
        original_player = game.current_player
        game.current_player = self.player_index  # Set to this bot's perspective
        
        heuristic = SungkaHeuristic(game)  # Fresh instance with current game state
        valid_moves = game.get_valid_moves(self.player_index)
        
        if not valid_moves:
            game.current_player = original_player  # Restore original
            return None
        
        # Get scored moves using the heuristic
        scored = []
        for move in valid_moves:
            try:
                score, _ = heuristic.evaluate_move_verbose(move)
                scored.append((move, score))
            except Exception as e:
                print(f"Heuristic evaluation failed for move {move}: {e}")
                scored.append((move, -1000))
        
        game.current_player = original_player  # Restore original
        
        if not scored:
            return valid_moves[0] if valid_moves else None
            
        return max(scored, key=lambda x: x[1])[0]

class Simulator:
    def __init__(self, opponent_type, num_simulations=100, max_moves_per_game=200, random_seed=None, save_excel=True, save_directory=None):
        self.opponent_type = opponent_type
        self.num_simulations = num_simulations
        self.max_moves_per_game = max_moves_per_game
        self.save_excel = save_excel
        if random_seed is not None:
            random.seed(random_seed)
        self.per_game_rows = []
        
        # Set save directory
        if save_directory is None:
            # Default save directory - CHANGE THIS to your preferred location
            save_directory = "F:/Oppah~/Programs/thesis/from dylan/simulation_results/"  # Your custom default path
            # Alternative: save_directory = "./" for current directory
        
        # Normalize the path and handle spaces properly
        self.save_directory = os.path.normpath(save_directory)
        
        # Create directory if it doesn't exist
        try:
            if not os.path.exists(self.save_directory):
                os.makedirs(self.save_directory)
                print(f"📁 Created directory: {self.save_directory}")
        except Exception as e:
            print(f"⚠️ Warning: Could not create directory '{self.save_directory}': {e}")
            print("📂 Falling back to current directory")
            self.save_directory = "./"

    def get_heuristic_move(self, game, player_index):
        """✅ FIXED: Create fresh heuristic instance for each move evaluation"""
        valid_moves = game.get_valid_moves(player_index)
        if not valid_moves:
            return None
        
        # Temporarily set the game's current player for proper heuristic evaluation
        original_player = game.current_player
        game.current_player = player_index
        
        # Create fresh heuristic instance with current game state
        heuristic = SungkaHeuristic(game)
        
        scored = []
        for move in valid_moves:
            try:
                score, _ = heuristic.evaluate_move_verbose(move)
                scored.append((move, score))
            except Exception as e:
                print(f"Heuristic evaluation failed for move {move}: {e}")
                scored.append((move, -1000))
        
        # Restore original current player
        game.current_player = original_player
        
        if not scored:
            return valid_moves[0] if valid_moves else None
            
        return max(scored, key=lambda x: x[1])[0]

    def get_opponent_bot(self, player_index):
        if self.opponent_type == 1:
            return RandomBot(player_index)
        elif self.opponent_type == 2:
            return BasicRuleBot(player_index)
        elif self.opponent_type == 3:
            return HeuristicBot(player_index)
        elif self.opponent_type == 4:
            return MaxPolicyBot(player_index)
        elif self.opponent_type == 5:
            return ExactPolicyBot(player_index)

  # Key fix: Replace the simulate_single_game method in your fixed_simulator.py
# with this corrected version that properly tracks heuristic player metrics

def simulate_single_game(self, game_number, heuristic_goes_first=True, enable_detailed_logging=False):
    game = SungkaGame()
    
    # Initialize logger for detailed logging if enabled
    logger = None
    if enable_detailed_logging:
        logger = GameLogger(save_directory=self.save_directory)

    # Set starting player based on turn order scenario
    if heuristic_goes_first:
        game.current_player = 0  # Heuristic is Player 1 (goes first)
        heuristic_player = 0
        opponent_player = 1
    else:
        game.current_player = 1  # Opponent is Player 1 (goes first), Heuristic is Player 2
        heuristic_player = 1
        opponent_player = 0

    # Create opponent bot (for heuristic vs heuristic, both use HeuristicBot)
    opponent = self.get_opponent_bot(opponent_player)
    move_count = 0

    # Track heuristic-specific metrics
    heuristic_metrics = {
        "marbles_captured": 0,
        "extra_turns": 0,
        "burned_created": 0,
        "burned_suffered": 0,
        "moves": 0
    }

    if logger:
        logger.record_move(game, "Game Started")

    while not game.is_game_over() and move_count < self.max_moves_per_game:
        current_player = game.current_player
        
        # Check if current player has valid moves
        valid_moves = game.get_valid_moves(current_player)
        if not valid_moves:
            game.collect_remaining_stones()
            break

        # Store board state before move
        board_before = game.board.copy()
        score_before = (game.board[7], game.board[15])
        burned_before = {0: set(game.burned_holes[0]), 1: set(game.burned_holes[1])}

        if current_player == heuristic_player:
            # Heuristic player's turn
            move = self.get_heuristic_move(game, heuristic_player)
        else:
            # Opponent bot
            move = opponent.get_move(game)

        if move is None:
            game.collect_remaining_stones()
            break

        try:
            result = game.play_turn(move)
            move_count += 1
            
            # Calculate what happened in this move
            score_after = (game.board[7], game.board[15])
            burned_after = game.burned_holes
            
            # Track metrics ONLY for the heuristic player
            if current_player == heuristic_player:
                # Calculate stones captured by heuristic player
                if heuristic_player == 0:
                    stones_captured = score_after[0] - score_before[0]
                else:
                    stones_captured = score_after[1] - score_before[1]
                
                heuristic_metrics["marbles_captured"] += max(0, stones_captured)
                heuristic_metrics["extra_turns"] += 1 if (result == "Extra Turn") else 0
                heuristic_metrics["moves"] += 1
                
                # Track burned holes created BY heuristic player
                burned_created = len(burned_after[heuristic_player] - burned_before[heuristic_player])
                heuristic_metrics["burned_created"] += burned_created
                
                # Track burned holes created AGAINST heuristic player (by opponent)
                burned_suffered = len(burned_after[opponent_player] - burned_before[opponent_player])
                heuristic_metrics["burned_suffered"] += burned_suffered
            
            extra_turn = (result == "Extra Turn")
            
            # Find new burned holes for logging
            burned_holes_created = []
            for player_idx in [0, 1]:
                new_burns = burned_after[player_idx] - burned_before[player_idx]
                burned_holes_created.extend(list(new_burns))
            
            # Log detailed move if logger is enabled
            if logger:
                stones_captured_this_move = 0
                if current_player == 0:
                    stones_captured_this_move = score_after[0] - score_before[0]
                else:
                    stones_captured_this_move = score_after[1] - score_before[1]
                
                logger.record_move(game, result, move)
                logger.record_detailed_move(
                    game=game,
                    hole_selected=move,
                    board_before=board_before,
                    action_result=result,
                    stones_captured=stones_captured_this_move,
                    extra_turn=extra_turn,
                    burned_holes_created=burned_holes_created
                )
            
            if result == "Game Over":
                break
                
        except ValueError as e:
            print(f"Invalid move attempted: {e}")
            game.collect_remaining_stones()
            break

    winner = game.get_winner()
    
    # Calculate score difference (heuristic_score - opponent_score)
    heuristic_score = game.board[7] if heuristic_player == 0 else game.board[15]
    opponent_score = game.board[15] if heuristic_player == 0 else game.board[7]
    score_difference = heuristic_score - opponent_score
    
    # Calculate absolute score difference (always positive)
    abs_score_difference = abs(score_difference)
    
    # Determine if heuristic won
    heuristic_won = None
    if winner is not None:
        heuristic_won = (winner == heuristic_player)

    # Save detailed log if enabled
    if logger:
        logger.record_move(game, f"Game Over - Winner: {winner}" if winner else "Game Over - Draw")
        logger.save_to_excel()

    # Record game results using heuristic-specific metrics
    row = {
        'game_number': game_number,
        'heuristic_goes_first': heuristic_goes_first,
        'heuristic_player_index': heuristic_player,
        'winner': winner,
        'heuristic_won': heuristic_won,
        'final_p1_head': game.board[7],
        'final_p2_head': game.board[15],
        'heuristic_final_score': heuristic_score,
        'opponent_final_score': opponent_score,
        'score_difference': score_difference,
        'abs_score_difference': abs_score_difference,
        'moves_played': heuristic_metrics['moves'],  # Only heuristic moves
        'marbles_captured_by_heuristic': heuristic_metrics['marbles_captured'],
        'extra_turns_by_heuristic': heuristic_metrics['extra_turns'],
        'burned_created_by_heuristic': heuristic_metrics['burned_created'],
        'burned_suffered_by_heuristic': heuristic_metrics['burned_suffered'],
        'burned_holes_p0': ','.join(map(str, sorted(list(game.burned_holes[0])))) if game.burned_holes[0] else '',
        'burned_holes_p1': ','.join(map(str, sorted(list(game.burned_holes[1])))) if game.burned_holes[1] else ''
    }

    self.per_game_rows.append(row)
    return row

    def run_turn_order_analysis(self, enable_detailed_logging=False):
        """Run simulations testing both turn orders"""
        start = time.time()
        
        # Split simulations between first/second player scenarios
        first_player_games = self.num_simulations // 2
        second_player_games = self.num_simulations - first_player_games
        
        print(f"Running {first_player_games} games as first player...")
        for i in range(1, first_player_games + 1):
            if i % 10 == 0:
                print(f"  First player games: {i}/{first_player_games}")
            # Only log detailed moves for first few games to avoid too many files
            detailed_log = enable_detailed_logging and i <= 5
            self.simulate_single_game(i, heuristic_goes_first=True, enable_detailed_logging=detailed_log)
        
        print(f"Running {second_player_games} games as second player...")
        for i in range(first_player_games + 1, self.num_simulations + 1):
            if (i - first_player_games) % 10 == 0:
                print(f"  Second player games: {i - first_player_games}/{second_player_games}")
            # Only log detailed moves for first few games to avoid too many files
            detailed_log = enable_detailed_logging and (i - first_player_games) <= 5
            self.simulate_single_game(i, heuristic_goes_first=False, enable_detailed_logging=detailed_log)

        elapsed = time.time() - start
        df = pd.DataFrame(self.per_game_rows)
        
        self.analyze_results(df, elapsed)
        return df

    def run_standard(self, enable_detailed_logging=False):
        """Run standard simulation with random turn order"""
        start = time.time()

        for i in range(1, self.num_simulations + 1):
            if i % 10 == 0:
                print(f"Completed {i}/{self.num_simulations} simulations...")
            # Randomly choose who goes first
            heuristic_first = random.choice([True, False])
            # Only log detailed moves for first few games to avoid too many files
            detailed_log = enable_detailed_logging and i <= 5
            self.simulate_single_game(i, heuristic_goes_first=heuristic_first, enable_detailed_logging=detailed_log)

        elapsed = time.time() - start
        df = pd.DataFrame(self.per_game_rows)
        
        self.analyze_results(df, elapsed)
        return df

    def analyze_results(self, df, elapsed):
        """Analyze and print simulation results"""
        total = len(df)
        
        if total == 0:
            print("No games completed successfully.")
            return

        # Overall statistics
        heuristic_wins = df['heuristic_won'].eq(True).sum()
        opponent_wins = df['heuristic_won'].eq(False).sum()
        draws = df['heuristic_won'].isna().sum()

        # Score difference statistics
        avg_score_diff = df['score_difference'].mean()
        avg_abs_score_diff = df['abs_score_difference'].mean()
        median_score_diff = df['score_difference'].median()
        std_score_diff = df['score_difference'].std()
        max_score_diff = df['score_difference'].max()
        min_score_diff = df['score_difference'].min()

        # Turn order analysis
        first_player_df = df[df['heuristic_goes_first'] == True]
        second_player_df = df[df['heuristic_goes_first'] == False]
        
        first_wins = first_player_df['heuristic_won'].eq(True).sum() if len(first_player_df) > 0 else 0
        first_total = len(first_player_df)
        second_wins = second_player_df['heuristic_won'].eq(True).sum() if len(second_player_df) > 0 else 0
        second_total = len(second_player_df)
        
        # Score difference by turn order
        first_avg_score_diff = first_player_df['score_difference'].mean() if len(first_player_df) > 0 else 0
        second_avg_score_diff = second_player_df['score_difference'].mean() if len(second_player_df) > 0 else 0

        # Performance metrics
        total_moves = df['moves_played'].sum()
        if total_moves > 0:
            avg_capture = df['marbles_captured_by_heuristic'].sum() / total_moves
            avg_extra = df['extra_turns_by_heuristic'].sum() / total_moves
            avg_burn_created = df['burned_created_by_heuristic'].sum() / total_moves
            avg_burn_suffered = df['burned_suffered_by_heuristic'].sum() / total_moves
        else:
            avg_capture = avg_extra = avg_burn_created = avg_burn_suffered = 0

        # Count games with burned holes
        games_with_burns = len(df[(df['burned_holes_p0'] != '') | 
                                 (df['burned_holes_p1'] != '')])

        # Print results
        opponent_names = {
            1: 'Random',
            2: 'Realistic Basic Rules', 
            3: 'Heuristic vs Heuristic',
            4: 'Max Policy',
            5: 'Exact Policy'
        }
        
        print("\n" + "="*60)
        print("HEURISTIC PERFORMANCE ANALYSIS")
        print("="*60)
        print(f"Opponent Type: {self.opponent_type} ({opponent_names.get(self.opponent_type, 'Unknown')})")
        print(f"Total Games: {total}")
        print(f"Total Time: {elapsed:.2f} seconds")
        print(f"Average Game Length: {total_moves/total:.1f} moves" if total > 0 else "N/A")
        
        print("\n--- OVERALL RESULTS ---")
        print(f"Heuristic Wins: {heuristic_wins}/{total} ({heuristic_wins/total*100:.1f}%)")
        print(f"Opponent Wins: {opponent_wins}/{total} ({opponent_wins/total*100:.1f}%)")
        print(f"Draws: {draws}/{total} ({draws/total*100:.1f}%)")
        
        print("\n--- SCORE DIFFERENCE ANALYSIS ---")
        print(f"Average Score Difference (Heuristic - Opponent): {avg_score_diff:+.2f}")
        print(f"Average Absolute Score Difference: {avg_abs_score_diff:.2f}")
        print(f"Median Score Difference: {median_score_diff:+.2f}")
        print(f"Standard Deviation: {std_score_diff:.2f}")
        print(f"Maximum Score Difference: {max_score_diff:+.2f}")
        print(f"Minimum Score Difference: {min_score_diff:+.2f}")
        
        print("\n--- TURN ORDER ANALYSIS ---")
        if first_total > 0:
            print(f"As First Player:  {first_wins}/{first_total} ({first_wins/first_total*100:.1f}% wins)")
            print(f"   Avg Score Difference: {first_avg_score_diff:+.2f}")
        if second_total > 0:
            print(f"As Second Player: {second_wins}/{second_total} ({second_wins/second_total*100:.1f}% wins)")
            print(f"   Avg Score Difference: {second_avg_score_diff:+.2f}")
        
        if first_total > 0 and second_total > 0:
            first_rate = first_wins/first_total
            second_rate = second_wins/second_total
            advantage = first_rate - second_rate
            score_diff_advantage = first_avg_score_diff - second_avg_score_diff
            print(f"First Player Advantage: {advantage*100:+.1f} percentage points")
            print(f"First Player Score Advantage: {score_diff_advantage:+.2f} points")
        
        print("\n--- PERFORMANCE METRICS (Heuristic) ---")
        print(f"Avg Marbles Captured per Move: {avg_capture:.4f}")
        print(f"Avg Extra Turns per Move: {avg_extra:.4f}")
        print(f"Avg Burned Holes Created per Move: {avg_burn_created:.6f}")
        print(f"Avg Burned Holes Suffered per Move: {avg_burn_suffered:.6f}")
        print(f"Games with Burned Holes: {games_with_burns}/{total} ({games_with_burns/total*100:.1f}%)")
        
        print("="*60)

        if self.save_excel:
            timestamp = int(time.time())
            outname = f"simulation_results_{opponent_names.get(self.opponent_type, 'unknown').lower().replace(' ', '_')}_{timestamp}.xlsx"
            outpath = os.path.join(self.save_directory, outname)
            
            try:
                df.to_excel(outpath, index=False)
                print(f"Saved detailed results to: {outpath}")
            except Exception as e:
                print(f"Error saving simulation results: {e}")
                # Fallback to current directory
                df.to_excel(outname, index=False)
                print(f"Saved to fallback location: {outname}")

if __name__ == "__main__":
    print("🎮 ENHANCED SUNGKA SIMULATION")
    print("Choose opponent:")
    print("1 = Random Bot")
    print("2 = Basic Rules Bot") 
    print("3 = Heuristic vs Heuristic")
    print("4 = Max Policy Bot (always picks house with most stones)")
    print("5 = Exact Policy Bot (picks house where stones = distance to head)")
    
    while True:
        try:
            choice = int(input("Enter choice (1-5): "))
            if choice in [1, 2, 3, 4, 5]:
                break
            print("Please enter 1, 2, 3, 4, or 5.")
        except ValueError:
            print("Please enter a number.")
    
    print("\nChoose simulation type:")
    print("1 = Standard (random turn order)")
    print("2 = Turn Order Analysis (test first/second player scenarios)")
    
    while True:
        try:
            sim_type = int(input("Enter choice (1-2): "))
            if sim_type in [1, 2]:
                break
            print("Please enter 1 or 2.")
        except ValueError:
            print("Please enter a number.")
    
    # Ask about number of simulations
    while True:
        try:
            num_sims = int(input("Number of simulations (default 100): ") or "100")
            if num_sims > 0:
                break
            print("Please enter a positive number.")
        except ValueError:
            print("Please enter a number.")
    
    # Ask about detailed logging
    print("\nEnable detailed move logging for first 5 games? (Creates individual Excel files)")
    enable_logging = input("Enable detailed logging? (y/n, default n): ").lower().strip() == 'y'
    
    # Ask about save directory
    print(f"\nCurrent save directory: {os.getcwd()}")
    print("💡 Tip: Use forward slashes (/) or double backslashes (\\\\) in paths")
    print("💡 Avoid spaces in folder names if possible")
    custom_dir = input("Enter custom save directory (or press Enter for current directory): ").strip()
    
    save_dir = None
    if custom_dir:
        # Handle different path formats
        custom_dir = custom_dir.replace('\\', '/')  # Convert backslashes to forward slashes
        if ' ' in custom_dir:
            print("⚠️ Warning: Path contains spaces. This might cause issues.")
            suggestion = custom_dir.replace(' ', '_')
            use_suggestion = input(f"Use '{suggestion}' instead? (y/n): ").lower().strip()
            if use_suggestion == 'y':
                custom_dir = suggestion
        save_dir = custom_dir
    
    # Create simulator
    sim = Simulator(opponent_type=choice, num_simulations=num_sims, save_directory=save_dir)
    
    if sim_type == 1:
        print(f"\n🚀 Running {num_sims} games with random turn order...")
        if enable_logging:
            print("📝 Detailed logging enabled for first 5 games")
        sim.run_standard(enable_detailed_logging=enable_logging)
    else:
        print(f"\n🚀 Running turn order analysis with {num_sims} games...")
        if enable_logging:
            print("📝 Detailed logging enabled for first 5 games from each turn order")
        sim.run_turn_order_analysis(enable_detailed_logging=enable_logging)
    
    print("\n🎉 Simulation complete!")