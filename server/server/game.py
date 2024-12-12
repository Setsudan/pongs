import json
from uuid import uuid4


class PongGame:
    def __init__(self):
        self.paddle_height = 60
        self.paddle_width = 10
        self.ball_size = 10
        self.width = 800
        self.height = 600
        self.WIN_SCORE = 20
        
        # Game state
        self.paddles = {
            'player1': {'y': self.height // 2, 'score': 0},
            'player2': {'y': self.height // 2, 'score': 0}
        }
        self.ball = {
            'x': self.width // 2,
            'y': self.height // 2,
            'dx': 5,
            'dy': 5
        }
        self.game_started = False
        self.winner = None  # Will store the winning player
        
    def update_paddle(self, player, movement):
        """Update paddle position with bounds checking"""
        if self.winner:  # Don't allow movement if game is over
            return
            
        new_y = self.paddles[player]['y'] + movement
        if 0 <= new_y <= self.height - self.paddle_height:
            self.paddles[player]['y'] = new_y
            
    def update_ball(self):
        """Update ball position and handle collisions"""
        if not self.game_started or self.winner:
            return
            
        # Update position
        self.ball['x'] += self.ball['dx']
        self.ball['y'] += self.ball['dy']
        
        # Wall collisions
        if self.ball['y'] <= 0 or self.ball['y'] >= self.height - self.ball_size:
            self.ball['dy'] *= -1
            
        # Paddle collisions
        p1_x = 50
        p2_x = self.width - 50 - self.paddle_width
        
        # Player 1 paddle
        if (p1_x <= self.ball['x'] <= p1_x + self.paddle_width and
            self.paddles['player1']['y'] <= self.ball['y'] <= self.paddles['player1']['y'] + self.paddle_height):
            self.ball['dx'] *= -1
            self.ball['x'] = p1_x + self.paddle_width + 1
            
        # Player 2 paddle
        if (p2_x <= self.ball['x'] <= p2_x + self.paddle_width and
            self.paddles['player2']['y'] <= self.ball['y'] <= self.paddles['player2']['y'] + self.paddle_height):
            self.ball['dx'] *= -1
            self.ball['x'] = p2_x - 1
            
        # Score points
        if self.ball['x'] <= 0:
            self.paddles['player2']['score'] += 1
            if self.paddles['player2']['score'] >= self.WIN_SCORE:
                self.winner = 'player2'
            self._reset_ball()
        elif self.ball['x'] >= self.width:
            self.paddles['player1']['score'] += 1
            if self.paddles['player1']['score'] >= self.WIN_SCORE:
                self.winner = 'player1'
            self._reset_ball()
            
    def _reset_ball(self):
        """Reset ball to center after point scored"""
        self.ball['x'] = self.width // 2
        self.ball['y'] = self.height // 2
        self.ball['dx'] *= -1
        
    def get_state(self):
        """Return current game state as dictionary"""
        return {
            'paddles': self.paddles,
            'ball': self.ball,
            'game_started': self.game_started,
            'winner': self.winner
        }
import json
from uuid import uuid4

class GamePool:
    def __init__(self):
        self.waiting_players = []  # Players waiting to be matched
        self.active_games = {}     # Dictionary of active games
        self.player_to_game = {}   # Mapping of players to their current game
        
    def add_player(self, player_id, client_socket):
        """Add a new player to the pool system"""
        if len(self.waiting_players) > 0:
            # Match with waiting player
            opponent = self.waiting_players.pop(0)
            game_id = str(uuid4())  # Generate unique UUID for game
            
            # Create new game instance
            game = PongGame()
            game.game_started = True
            
            # Store game and player mappings
            self.active_games[game_id] = {
                'game': game,
                'players': {
                    'player1': opponent,
                    'player2': client_socket
                }
            }
            
            # Map both players to this game
            self.player_to_game[opponent] = game_id
            self.player_to_game[client_socket] = game_id
            
            # Notify both players they've been matched
            self._notify_players_matched(game_id)
            
            return game_id
        else:
            # Add to waiting list
            self.waiting_players.append(client_socket)
            self._notify_player_waiting(client_socket)
            return None
            
    def remove_player(self, client_socket):
        """Remove a player from the pool system"""
        # Remove from waiting list if present
        if client_socket in self.waiting_players:
            self.waiting_players.remove(client_socket)
            return
            
        # Handle removal from active game
        if client_socket in self.player_to_game:
            game_id = self.player_to_game[client_socket]
            if game_id in self.active_games:  # Check if game still exists
                game_info = self.active_games[game_id]
                
                # Notify other player about disconnection
                other_player = None
                for role, player in game_info['players'].items():
                    if player != client_socket:
                        other_player = player
                        break
                        
                if other_player:
                    # Remove game mappings
                    if client_socket in self.player_to_game:
                        del self.player_to_game[client_socket]
                    if other_player in self.player_to_game:
                        del self.player_to_game[other_player]
                    
                    # Add other player back to waiting list
                    self.waiting_players.append(other_player)
                    self._notify_player_waiting(other_player)
                    
                # Remove the game
                del self.active_games[game_id]
            else:
                # Clean up orphaned player mapping
                del self.player_to_game[client_socket]

    def get_game_for_player(self, client_socket):
        """Get the current game instance for a player"""
        if client_socket in self.player_to_game:
            game_id = self.player_to_game[client_socket]
            if game_id in self.active_games:  # Check if game still exists
                return self.active_games[game_id]['game']
        return None

    def get_player_role(self, client_socket):
        """Get the role (player1/player2) for a given player"""
        if client_socket in self.player_to_game:
            game_id = self.player_to_game[client_socket]
            if game_id in self.active_games:  # Check if game still exists
                players = self.active_games[game_id]['players']
                return 'player1' if players['player1'] == client_socket else 'player2'
        return None

    def _notify_players_matched(self, game_id):
        """Notify players they've been matched"""
        if game_id in self.active_games:  # Check if game still exists
            game_info = self.active_games[game_id]
            message = json.dumps({
                'type': 'game_start',
                'game_id': game_id
            }).encode()
            
            for player_socket in game_info['players'].values():
                try:
                    player_socket.send(message)
                except (BrokenPipeError, ConnectionResetError):
                    self.remove_player(player_socket)

    def _notify_player_waiting(self, client_socket):
        """Notify player they're in the waiting list"""
        try:
            message = json.dumps({
                'type': 'waiting',
                'position': self.waiting_players.index(client_socket)
            }).encode()
            client_socket.send(message)
        except (BrokenPipeError, ConnectionResetError):
            self.remove_player(client_socket)
            