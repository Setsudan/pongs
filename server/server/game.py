class PongGame:
    def __init__(self):
        self.paddle_height = 60
        self.paddle_width = 10
        self.ball_size = 10
        self.width = 800
        self.height = 600
        
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
        
    def update_paddle(self, player, movement):
        """Update paddle position with bounds checking"""
        new_y = self.paddles[player]['y'] + movement
        if 0 <= new_y <= self.height - self.paddle_height:
            self.paddles[player]['y'] = new_y
            
    def update_ball(self):
        """Update ball position and handle collisions"""
        if not self.game_started:
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
            self._reset_ball()
        elif self.ball['x'] >= self.width:
            self.paddles['player1']['score'] += 1
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
            'game_started': self.game_started
        }
