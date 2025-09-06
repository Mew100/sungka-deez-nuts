from main import SungkaGame
from game_logger import GameLogger
import os

def play_game_with_detailed_recording():
    print("🎮 SUNGKA GAME WITH DETAILED RECORDING")
    
    # Ask for save directory
    print(f"\nCurrent directory: {os.getcwd()}")
    custom_dir = input("Enter save directory (or press Enter for current directory): ").strip()
    save_dir = custom_dir if custom_dir else None
    
    game = SungkaGame()
    recorder = GameLogger(save_directory=save_dir)
    
    recorder.record_move(game, "Game Started")
    print(f"\n📝 Game will be saved to: {recorder.filepath}")
    
    move_number = 0
    
    while True:
        game.print_board_state()
        
        try:
            player_side = "1 (0-6)" if game.current_player == 0 else "2 (8-14)"
            hole = int(input(f"Player {game.current_player + 1}'s turn\n"
                           f"Choose a hole to distribute stones ({player_side}): "))
            
            # Store state before move
            board_before = game.board.copy()
            score_before = (game.board[7], game.board[15])
            burned_before = {0: set(game.burned_holes[0]), 1: set(game.burned_holes[1])}
            current_player = game.current_player
            move_number += 1
            
            # Record basic move info
            recorder.record_move(game, "Turn Started", hole)
            
            # Execute move
            result = game.play_turn(hole)
            
            # Calculate what happened in this move
            score_after = (game.board[7], game.board[15])
            burned_after = game.burned_holes
            
            stones_captured = 0
            if current_player == 0:
                stones_captured = score_after[0] - score_before[0]
            else:
                stones_captured = score_after[1] - score_before[1]
            
            extra_turn = (result == "Extra Turn")
            
            # Find new burned holes
            burned_holes_created = []
            for player_idx in [0, 1]:
                new_burns = burned_after[player_idx] - burned_before[player_idx]
                burned_holes_created.extend(list(new_burns))
            
            # Record detailed move
            recorder.record_detailed_move(
                game=game,
                hole_selected=hole,
                board_before=board_before,
                action_result=result,
                stones_captured=stones_captured,
                extra_turn=extra_turn,
                burned_holes_created=burned_holes_created
            )
            
            # Record result
            recorder.record_move(game, result)
            
            print(f"\n=== Turn {move_number} Result: {result} ===")
            if stones_captured > 0:
                print(f"💎 Stones captured: {stones_captured}")
            if burned_holes_created:
                print(f"🔥 Burned holes created: {burned_holes_created}")
            if extra_turn:
                print("🎯 Extra turn earned!")
            
            if result == "Game Over":
                game.print_board_state()
                winner = game.get_winner()
                if winner is not None:
                    print(f"\n🏆 Winner: Player {winner + 1} 🏆")
                    recorder.record_move(game, f"Game Over - Winner: Player {winner + 1}")
                else:
                    print("\n🤝 It's a draw! 🤝")
                    recorder.record_move(game, "Game Over - Draw")
                
                # Print final statistics
                print(f"\n📊 Final Scores:")
                print(f"Player 1: {game.board[7]} marbles")
                print(f"Player 2: {game.board[15]} marbles")
                print(f"Score difference: {abs(game.board[7] - game.board[15])}")
                print(f"Total moves played: {move_number}")
                
                break
                
        except ValueError as e:
            print(f"\nError: {e}")
            recorder.record_move(game, f"Invalid Move: {str(e)}")
            continue
        
        # Ask if player wants to continue (optional)
        if result != "Game Over" and result != "Extra Turn":
            cont = input("\nPress Enter to continue (or 'q' to quit): ").lower().strip()
            if cont == 'q':
                recorder.record_move(game, "Game Aborted by User")
                break
    
    # Save the detailed log
    recorder.save_to_excel()
    print(f"\n💾 Detailed game session saved!")
    print(f"📄 File location: {recorder.filepath}")
    print("📋 Excel file contains 3 sheets:")
    print("   • Session_Log: Basic game events")
    print("   • Detailed_Moves: Move-by-move analysis")
    print("   • Game_Statistics: Summary statistics")

def play_quick_game():
    """Quick game without detailed logging (original functionality)"""
    game = SungkaGame()
    recorder = GameLogger()
    
    recorder.record_move(game, "Game Started")
    
    while True:
        game.print_board_state()
        
        try:
            player_side = "1 (0-6)" if game.current_player == 0 else "2 (8-14)"
            hole = int(input(f"Player {game.current_player + 1}'s turn\n"
                           f"Choose a hole to distribute stones ({player_side}): "))
            
            recorder.record_move(game, "Turn Started", hole)
            result = game.play_turn(hole)
            recorder.record_move(game, result)
            
            print("Turn result:", result)
            
            if result == "Game Over":
                game.print_board_state()
                winner = game.get_winner()
                if winner is not None:
                    print(f"Winner: Player {winner + 1}")
                else:
                    print("It's a draw!")
                recorder.record_move(game, f"Game Over - Winner: {winner}" if winner else "Game Over - Draw")
                break
        
        except ValueError as e:
            print("Error:", str(e))
            recorder.record_move(game, f"Invalid Move: {str(e)}")
        
        cont = input("Continue? (y/n): ").lower()
        if cont != 'y':
            recorder.record_move(game, "Game Aborted by User")
            break
    
    recorder.save_to_excel()
    print("Basic game session recorded")

if __name__ == "__main__":
    print("Choose game mode:")
    print("1 = Detailed Recording (recommended)")
    print("2 = Quick Game (basic logging)")
    
    while True:
        try:
            choice = int(input("Enter choice (1-2): "))
            if choice in [1, 2]:
                break
            print("Please enter 1 or 2.")
        except ValueError:
            print("Please enter a number.")
    
    if choice == 1:
        play_game_with_detailed_recording()
    else:
        play_quick_game()