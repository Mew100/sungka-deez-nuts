# sungka-deez-nuts
thesis moment

####changelogs:

09/06/2025 - 1:11pm
- modified code to have close to equal win-rates against heuristic vs heuristic
        - To use whichever heuristic file you want to test:
            from balanced_heuristic import SungkaHeuristic (your original balanced one)
            from more_balanced_heuristic import SungkaHeuristic (the more aggressive one I created)
            from heuristic import SungkaHeuristic (your original heuristic)
- do download latest files (try only downloading more-balanced-heuristic, complete-working-simulator.py, game_logger.py, main.py, and play_game.py and see if it works) idk what play_ game.py does try excluding it too.

09/01/2025 - 12:41am: 
- added feature to choose directory to store game logs (also creates folder)[issues when folder created has spaces]
- changed def collect_remaining_stones(self): to get remaining stones remaining if one side is empty (game ends)

If Player 1’s side (holes 0–6) becomes empty → the game ends immediately.

The remaining shells on Player 2’s side (holes 8–14) are collected into Player 2’s head (hole 15).

And vice versa:

If Player 2’s side (holes 8–14) becomes empty → the game ends.

The remaining shells on Player 1’s side (holes 0–6) are collected into Player 1’s head (hole 7).
