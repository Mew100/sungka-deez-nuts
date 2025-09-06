# more_balanced_heuristic.py
import numpy as np
import random

class SungkaHeuristic:
    def __init__(self, game):
        self.original_game = game

    def simulate_move_complete(self, game, hole):
        """Complete move simulation with proper burned hole handling and relay"""
        board = game.board.copy()
        current_player = game.current_player
        burned_holes = {0: set(game.burned_holes[0]), 1: set(game.burned_holes[1])}

        if hole in burned_holes[current_player]:
            return None
        if not ((current_player == 0 and 0 <= hole <= 6 and board[hole] > 0) or
                (current_player == 1 and 8 <= hole <= 14 and board[hole] > 0)):
            return None

        originally_empty = set(i for i in range(16) if board[i] == 0)
        
        total_captured = 0
        extra_turns = 0
        burns_created = 0
        
        def distribute_from_hole(start_hole):
            nonlocal total_captured, extra_turns, burns_created
            
            stones = board[start_hole]
            board[start_hole] = 0
            current_hole = start_hole

            while stones > 0:
                current_hole = (current_hole + 1) % 16
                
                # Skip opponent's head
                if (current_player == 0 and current_hole == 15) or (current_player == 1 and current_hole == 7):
                    continue
                    
                # Skip burned holes
                if current_hole in burned_holes[0] or current_hole in burned_holes[1]:
                    continue
                    
                board[current_hole] += 1
                stones -= 1

            # Check for extra turn
            if (current_player == 0 and current_hole == 7) or (current_player == 1 and current_hole == 15):
                extra_turns += 1
                return current_hole, True
            
            # Check for relay (continue distribution)
            if current_hole not in (7, 15) and board[current_hole] > 1:
                return distribute_from_hole(current_hole)
            
            # Check for capture
            if ((current_player == 0 and 0 <= current_hole <= 6 and board[current_hole] == 1) or
                (current_player == 1 and 8 <= current_hole <= 14 and board[current_hole] == 1)):
                opposite_hole = 14 - current_hole
                if board[opposite_hole] > 0:
                    # Capture occurs
                    captured = board[current_hole] + board[opposite_hole]
                    total_captured += captured
                    head = 7 if current_player == 0 else 15
                    board[head] += captured
                    board[current_hole] = 0
                    board[opposite_hole] = 0
                elif board[opposite_hole] == 0:
                    # Sunog occurs - but only if landing in originally empty hole
                    if current_hole in originally_empty:
                        seeds = board[current_hole]
                        board[current_hole] = 0
                        opponent_head = 15 if current_player == 0 else 7
                        board[opponent_head] += seeds
                        burned_holes[current_player].add(current_hole)
                        burns_created += 1

            return current_hole, False

        last_hole, got_extra_turn = distribute_from_hole(hole)
        
        return {
            'board': board,
            'burned_holes': burned_holes,
            'total_captured': total_captured,
            'extra_turns': extra_turns,
            'burns_created': burns_created,
            'last_hole': last_hole
        }

    def analyze_opponent_threats(self, game, board_after, evaluating_player):
        """Analyze immediate threats from opponent relative to evaluating player"""
        opponent = 1 - evaluating_player
        threat_score = 0
        
        opponent_range = range(8, 15) if evaluating_player == 0 else range(0, 7)
        my_range = range(0, 7) if evaluating_player == 0 else range(8, 15)
        
        for opp_hole in opponent_range:
            if board_after[opp_hole] == 0 or opp_hole in game.burned_holes[opponent]:
                continue
                
            stones = board_after[opp_hole]
            
            # Simple simulation of opponent's potential move
            current_hole = opp_hole
            temp_stones = stones
            
            while temp_stones > 0:
                current_hole = (current_hole + 1) % 16
                
                # Skip our head
                if (opponent == 0 and current_hole == 15) or (opponent == 1 and current_hole == 7):
                    continue
                    
                temp_stones -= 1
            
            # Check what opponent could achieve
            if ((opponent == 0 and current_hole == 7) or (opponent == 1 and current_hole == 15)):
                threat_score -= 3  # Further reduced threat penalty
            elif ((opponent == 0 and 0 <= current_hole <= 6) or 
                  (opponent == 1 and 8 <= current_hole <= 14)):
                opposite = 14 - current_hole
                if board_after[current_hole] == 1 and board_after[opposite] > 0:
                    threat_score -= board_after[opposite] * 1.0  # Further reduced threat penalty
        
        return threat_score

    def evaluate_endgame_strategy(self, game, board_after, evaluating_player):
        """More balanced endgame evaluation for any player"""
        if evaluating_player == 0:
            my_head = board_after[7]
            opponent_head = board_after[15]
            my_stones = sum(board_after[0:7])
            opponent_stones = sum(board_after[8:15])
        else:
            my_head = board_after[15]
            opponent_head = board_after[7]
            my_stones = sum(board_after[8:15])
            opponent_stones = sum(board_after[0:7])
        
        total_remaining = my_stones + opponent_stones
        
        if total_remaining <= 25:  # Slightly higher endgame threshold
            head_diff = my_head - opponent_head
            
            # More balanced endgame strategy
            if head_diff > 3:  # Only if significantly ahead
                # Leading: try to safely clear
                clear_bonus = max(0, (15 - my_stones)) * 1.5  # Reduced from 2
                return head_diff * 10 + clear_bonus  # Reduced from 12
            elif head_diff < -3:  # Only if significantly behind
                # Behind: try to gain stones
                if my_stones > opponent_stones:
                    comeback_bonus = (my_stones - opponent_stones) * 2.5  # Reduced from 3
                    return head_diff * 10 + comeback_bonus  # Reduced from 12
                else:
                    return head_diff * 12  # Reduced from 15
            else:
                # Close game: maintain material advantage
                return (my_stones - opponent_stones) * 4  # Reduced from 5
        
        return 0

    def evaluate_move_verbose(self, hole):
        game = self.original_game
        evaluating_player = game.current_player  # The player making this move
        
        # Simulate the complete move
        result = self.simulate_move_complete(game, hole)
        if result is None:
            return -float('inf'), {"Error": "Invalid move"}

        board_after = result['board']
        scores = {}
        
        # Calculate game progress
        total_stones_on_board = sum(board_after[i] for i in range(16) if i not in (7, 15))
        game_progress = 1 - (total_stones_on_board / 98)
        
        # 1. Immediate tactical gains - Slightly more aggressive
        capture_score = result['total_captured'] * 11  # Increased from 10
        extra_turn_score = result['extra_turns'] * 16   # Increased from 15  
        burn_penalty = result['burns_created'] * -18    # Reduced penalty from -20
        
        scores['Captures'] = capture_score
        scores['Extra Turns'] = extra_turn_score
        scores['Burn Penalty'] = burn_penalty
        
        # 2. Strategic position evaluation (relative to evaluating player)
        if evaluating_player == 0:
            my_head = board_after[7]
            opponent_head = board_after[15]
            my_stones = sum(board_after[0:7])
            opponent_stones = sum(board_after[8:15])
            my_range = range(0, 7)
        else:
            my_head = board_after[15]
            opponent_head = board_after[7]
            my_stones = sum(board_after[8:15])
            opponent_stones = sum(board_after[0:7])
            my_range = range(8, 15)
        
        head_diff = my_head - opponent_head
        material_diff = my_stones - opponent_stones
        
        # More aggressive dynamic scoring based on game phase
        if game_progress < 0.3:  # Early game
            scores['Head Advantage'] = head_diff * 7  # Increased from 6
            scores['Material Control'] = material_diff * 2.5  # Increased from 2
            
            # More balanced development scoring
            active_holes = sum(1 for i in my_range if board_after[i] > 0)
            if active_holes >= 5:
                scores['Development'] = 6  # Increased from 5
            elif active_holes <= 2:
                scores['Development'] = -8  # Reduced penalty from -10
            else:
                scores['Development'] = 0
                
        elif game_progress > 0.6:  # Late game
            endgame_score = self.evaluate_endgame_strategy(game, board_after, evaluating_player)
            scores['Endgame Strategy'] = endgame_score
            scores['Material Control'] = material_diff * 1.0  # Increased from 0.8
            
        else:  # Mid game - More aggressive
            scores['Head Advantage'] = head_diff * 9  # Increased from 8
            scores['Material Control'] = material_diff * 1.8  # Increased from 1.5
            
            # More aggressive mid-game tactical focus
            active_holes = sum(1 for i in my_range if board_after[i] > 0)
            if active_holes >= 3:
                scores['Flexibility'] = 4  # Increased from 3
            else:
                scores['Flexibility'] = -4  # Reduced penalty from -5
        
        # 3. Reduced threat analysis weight
        threat_score = self.analyze_opponent_threats(game, board_after, evaluating_player)
        scores['Threat Analysis'] = threat_score * 0.8  # Reduce impact of threats
        
        # 4. More aggressive move efficiency
        stones_used = game.board[hole]
        efficiency_score = 0
        
        # Reward efficient captures and extra turns more
        if result['total_captured'] > 0:
            efficiency = result['total_captured'] / max(1, stones_used)
            efficiency_score += efficiency * 6  # Increased from 5
        
        if result['extra_turns'] > 0:
            if stones_used <= 6:
                efficiency_score += 5  # Increased from 4
            else:
                efficiency_score += 2  # Increased from 1
        
        # Reduced penalty for wasteful large moves
        if stones_used > 12 and result['total_captured'] == 0 and result['extra_turns'] == 0:
            efficiency_score -= 3  # Reduced from -4
        
        scores['Move Efficiency'] = efficiency_score
        
        # 5. More aggressive tactical considerations
        tactical_score = 0
        
        # Count immediate capture opportunities after this move
        for next_hole in my_range:
            if board_after[next_hole] == 0 or next_hole in game.burned_holes[evaluating_player]:
                continue
            next_stones = board_after[next_hole]
            landing = (next_hole + next_stones) % 16
            
            # Adjust for player boundaries
            if evaluating_player == 1 and landing < 8:
                continue
            if evaluating_player == 0 and landing > 6 and landing != 7:
                continue
                
            if ((evaluating_player == 0 and 0 <= landing <= 6) or
                (evaluating_player == 1 and 8 <= landing <= 14)):
                if board_after[landing] == 0:
                    opposite = 14 - landing
                    if board_after[opposite] > 0:
                        tactical_score += board_after[opposite] * 0.4  # Increased from 0.3
        
        scores['Tactical Setup'] = tactical_score
        
        # 6. Slightly increased randomization for variety
        if game_progress > 0.1:
            randomization = random.uniform(-1.5, 1.5)  # Increased from (-1, 1)
            scores['Variation'] = randomization
        else:
            scores['Variation'] = 0
        
        # 7. Enhanced turn order balance compensation
        turn_balance = 0
        if game.metrics['moves'] < 6:  # Extended early game compensation
            if evaluating_player == 1:  # Second player
                turn_balance = 1.5  # Increased bonus for second player
        scores['Turn Balance'] = turn_balance
        
        # 8. NEW: Positional bonus for maintaining board control
        positional_score = 0
        if game_progress < 0.7:  # Don't apply in endgame
            # Bonus for having stones in multiple holes (flexibility)
            non_empty_holes = sum(1 for i in my_range if board_after[i] > 0)
            if non_empty_holes >= 4:
                positional_score += 2
            elif non_empty_holes <= 1:
                positional_score -= 3
            
            # Bonus for having moderate stone counts (avoid concentration)
            moderate_holes = sum(1 for i in my_range if 3 <= board_after[i] <= 8)
            positional_score += moderate_holes * 0.5
        
        scores['Positional Control'] = positional_score
        
        # Total score calculation
        total_score = sum(scores.values())
        
        # Add context info
        scores['Stones Used'] = stones_used
        scores['Total Score'] = total_score
        
        return total_score, scores