# balanced_heuristic.py
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
                threat_score -= 4  # Reduced threat penalty
            elif ((opponent == 0 and 0 <= current_hole <= 6) or 
                  (opponent == 1 and 8 <= current_hole <= 14)):
                opposite = 14 - current_hole
                if board_after[current_hole] == 1 and board_after[opposite] > 0:
                    threat_score -= board_after[opposite] * 1.5  # Reduced threat penalty
        
        return threat_score

    def evaluate_endgame_strategy(self, game, board_after, evaluating_player):
        """Balanced endgame evaluation for any player"""
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
        
        if total_remaining <= 20:  # Endgame threshold
            head_diff = my_head - opponent_head
            
            # Balanced endgame strategy
            if head_diff > 0:
                # Leading: try to safely clear
                clear_bonus = max(0, (15 - my_stones)) * 2
                return head_diff * 12 + clear_bonus
            elif head_diff < 0:
                # Behind: try to gain stones
                if my_stones > opponent_stones:
                    comeback_bonus = (my_stones - opponent_stones) * 3
                    return head_diff * 12 + comeback_bonus
                else:
                    return head_diff * 15
            else:
                # Tied: maintain material advantage
                return (my_stones - opponent_stones) * 5
        
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
        
        # 1. Immediate tactical gains (always positive for good moves)
        capture_score = result['total_captured'] * 10  # Reduced from 12
        extra_turn_score = result['extra_turns'] * 15   # Reduced from 20
        burn_penalty = result['burns_created'] * -20    # Reduced penalty from -30
        
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
        
        # Balanced dynamic scoring based on game phase
        if game_progress < 0.3:  # Early game
            scores['Head Advantage'] = head_diff * 6  # Reduced from 8
            scores['Material Control'] = material_diff * 2  # Reduced from 3
            
            # Balanced development scoring
            active_holes = sum(1 for i in my_range if board_after[i] > 0)
            if active_holes >= 5:
                scores['Development'] = 5  # Reduced from 8
            elif active_holes <= 2:
                scores['Development'] = -10  # Reduced penalty from -15
            else:
                scores['Development'] = 0
                
        elif game_progress > 0.6:  # Late game
            endgame_score = self.evaluate_endgame_strategy(game, board_after, evaluating_player)
            scores['Endgame Strategy'] = endgame_score
            scores['Material Control'] = material_diff * 0.8  # Reduced from 1
            
        else:  # Mid game
            scores['Head Advantage'] = head_diff * 8  # Reduced from 10
            scores['Material Control'] = material_diff * 1.5  # Reduced from 2
            
            # Balanced mid-game tactical focus
            active_holes = sum(1 for i in my_range if board_after[i] > 0)
            if active_holes >= 3:
                scores['Flexibility'] = 3  # Reduced from 5
            else:
                scores['Flexibility'] = -5  # Reduced penalty from -8
        
        # 3. Balanced threat analysis
        threat_score = self.analyze_opponent_threats(game, board_after, evaluating_player)
        scores['Threat Analysis'] = threat_score
        
        # 4. Balanced move efficiency
        stones_used = game.board[hole]
        efficiency_score = 0
        
        # Reward efficient captures and extra turns
        if result['total_captured'] > 0:
            efficiency = result['total_captured'] / max(1, stones_used)
            efficiency_score += efficiency * 5  # Reduced from 8
        
        if result['extra_turns'] > 0:
            if stones_used <= 6:
                efficiency_score += 4  # Reduced from 6
            else:
                efficiency_score += 1  # Reduced from 2
        
        # Reduced penalty for wasteful large moves
        if stones_used > 12 and result['total_captured'] == 0 and result['extra_turns'] == 0:
            efficiency_score -= 4  # Reduced from -8
        
        scores['Move Efficiency'] = efficiency_score
        
        # 5. Balanced tactical considerations
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
                        tactical_score += board_after[opposite] * 0.3  # Reduced from 0.5
        
        scores['Tactical Setup'] = tactical_score
        
        # 6. Smaller randomization to reduce deterministic play
        if game_progress > 0.1:
            randomization = random.uniform(-1, 1)  # Reduced from (-2, 2)
            scores['Variation'] = randomization
        else:
            scores['Variation'] = 0
        
        # 7. Turn order balance compensation
        # Add slight compensation for second player to balance first-move advantage
        turn_balance = 0
        if game.metrics['moves'] < 4:  # Only in very early game
            if evaluating_player == 1:  # Second player
                turn_balance = 1  # Small bonus for second player in early game
        scores['Turn Balance'] = turn_balance
        
        # Total score calculation
        total_score = sum(scores.values())
        
        # Add context info
        scores['Stones Used'] = stones_used
        scores['Total Score'] = total_score
        
        return total_score, scores