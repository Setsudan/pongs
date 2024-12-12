import pygame
import socket
import json
import threading
import sys

class PongClient:
    def __init__(self, host='localhost', port=5000):
        # Initialize Pygame
        pygame.init()
        self.width = 800
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Multiplayer Pong - Pool System")
        
        # Game objects dimensions
        self.paddle_height = 60
        self.paddle_width = 10
        self.ball_size = 10
        
        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GRAY = (128, 128, 128)
        
        # Game state
        self.game_state = {
            'paddles': {
                'player1': {'y': self.height // 2, 'score': 0},
                'player2': {'y': self.height // 2, 'score': 0}
            },
            'ball': {
                'x': self.width // 2,
                'y': self.height // 2,
                'dx': 5,
                'dy': 5
            },
            'game_started': False
        }
        
        # Pool system state
        self.in_queue = False
        self.queue_position = 0
        self.game_id = None
        
        # Network setup
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((host, port))
            print("Connected to server")
        except ConnectionRefusedError:
            print("Could not connect to server")
            sys.exit()
            
        # Start network thread
        self.running = True
        self.network_thread = threading.Thread(target=self._handle_network)
        self.network_thread.daemon = True
        self.network_thread.start()
        
        # Fonts
        self.score_font = pygame.font.Font(None, 74)
        self.message_font = pygame.font.Font(None, 36)
        
        # Clock for controlling frame rate
        self.clock = pygame.time.Clock()
        
    def _handle_network(self):
        """Handle network communication in separate thread"""
        while self.running:
            try:
                data = self.socket.recv(1024).decode()
                if not data:
                    break
                    
                messages = data.split('\n')
                for message in messages:
                    if not message:
                        continue
                    try:
                        parsed = json.loads(message)
                        if parsed['type'] == 'game_state':
                            self.game_state = parsed['state']
                        elif parsed['type'] == 'waiting':
                            self.in_queue = True
                            self.queue_position = parsed['position']
                            self.game_state['game_started'] = False
                        elif parsed['type'] == 'game_start':
                            self.in_queue = False
                            self.game_id = parsed['game_id']
                            self.game_state['game_started'] = True
                        elif parsed['type'] == 'error':
                            print("Server error:", parsed['message'])
                            self.running = False
                            break
                    except json.JSONDecodeError:
                        print("Error parsing message:", message)
                        
            except ConnectionResetError:
                print("Lost connection to server")
                self.running = False
                break
                
    def _draw_queue_status(self):
        """Draw the queue status message"""
        messages = []
        if self.in_queue:
            messages.append(f"You are in position {self.queue_position + 1} in the queue")
            messages.append("Waiting for another player...")
        else:
            messages.append("Connecting to server...")
            
        y_offset = self.height // 2 - (len(messages) * 30)
        for message in messages:
            text = self.message_font.render(message, True, self.WHITE)
            text_rect = text.get_rect(center=(self.width//2, y_offset))
            self.screen.blit(text, text_rect)
            y_offset += 60
            
    def _draw_game_id(self):
        """Draw the current game ID"""
        if self.game_id:
            text = self.message_font.render(f"Game: {self.game_id}", True, self.GRAY)
            text_rect = text.get_rect(topleft=(10, 10))
            self.screen.blit(text, text_rect)
            
    def run(self):
        """Main game loop"""
        movement_speed = 5
        
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE and 'winner' in self.game_state and self.game_state['winner']:
                        self.running = False
                    
            # Handle continuous keyboard input only when in game
            if self.game_state['game_started']:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_UP]:
                    self._send_movement(-movement_speed)
                elif keys[pygame.K_DOWN]:
                    self._send_movement(movement_speed)
                    
            # Clear screen
            self.screen.fill(self.BLACK)
            
            if not self.game_state['game_started']:
                self._draw_queue_status()
            else:
                # Draw game objects
                self._draw_paddle(50, self.game_state['paddles']['player1']['y'])
                self._draw_paddle(self.width - 50 - self.paddle_width,
                                self.game_state['paddles']['player2']['y'])
                self._draw_ball(self.game_state['ball']['x'],
                              self.game_state['ball']['y'])
                self._draw_scores()
                
                # Draw winner message if game is over
                if 'winner' in self.game_state and self.game_state['winner']:
                    winner_text = f"Player {self.game_state['winner'][-1]} Wins!"
                    text = self.message_font.render(winner_text, True, self.WHITE)
                    text_rect = text.get_rect(center=(self.width//2, self.height//2))
                    self.screen.blit(text, text_rect)
                    
                    # Draw restart instruction
                    restart_text = "Press ESC to leave the game"
                    text = self.message_font.render(restart_text, True, self.GRAY)
                    text_rect = text.get_rect(center=(self.width//2, self.height//2 + 40))
                    self.screen.blit(text, text_rect)
                
            # Always draw game ID if available
            self._draw_game_id()
                
            # Update display
            pygame.display.flip()
            
            # Control frame rate
            self.clock.tick(60)
            
        # Cleanup
        self.socket.close()
        pygame.quit()
        
    def _send_movement(self, movement):
        """Send movement update to server"""
        try:
            message = json.dumps({
                'type': 'move',
                'movement': movement
            })
            self.socket.send(message.encode())
        except (BrokenPipeError, ConnectionResetError):
            self.running = False
            
    def _draw_paddle(self, x, y):
        """Draw a paddle at the specified position"""
        pygame.draw.rect(self.screen, self.WHITE, 
                        (x, y, self.paddle_width, self.paddle_height))
        
    def _draw_ball(self, x, y):
        """Draw the ball at the specified position"""
        pygame.draw.rect(self.screen, self.WHITE,
                        (x, y, self.ball_size, self.ball_size))
        
    def _draw_scores(self):
        """Draw the current scores"""
        # Player 1 score
        score1 = self.score_font.render(
            str(self.game_state['paddles']['player1']['score']), True, self.WHITE)
        self.screen.blit(score1, (self.width//4, 50))
        
        # Player 2 score
        score2 = self.score_font.render(
            str(self.game_state['paddles']['player2']['score']), True, self.WHITE)
        self.screen.blit(score2, (3*self.width//4, 50))
    def __init__(self, host='localhost', port=5000):
        # Initialize Pygame
        pygame.init()
        self.width = 800
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Multiplayer Pong - Pool System")
        
        # Game objects dimensions
        self.paddle_height = 60
        self.paddle_width = 10
        self.ball_size = 10
        
        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GRAY = (128, 128, 128)
        
        # Game state
        self.game_state = {
            'paddles': {
                'player1': {'y': self.height // 2, 'score': 0},
                'player2': {'y': self.height // 2, 'score': 0}
            },
            'ball': {
                'x': self.width // 2,
                'y': self.height // 2,
                'dx': 5,
                'dy': 5
            },
            'game_started': False
        }
        
        # Pool system state
        self.in_queue = False
        self.queue_position = 0
        self.game_id = None
        
        # Network setup
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((host, port))
            print("Connected to server")
        except ConnectionRefusedError:
            print("Could not connect to server")
            sys.exit()
            
        # Start network thread
        self.running = True
        self.network_thread = threading.Thread(target=self._handle_network)
        self.network_thread.daemon = True
        self.network_thread.start()
        
        # Fonts
        self.score_font = pygame.font.Font(None, 74)
        self.message_font = pygame.font.Font(None, 36)
        
        # Clock for controlling frame rate
        self.clock = pygame.time.Clock()
        
    def _handle_network(self):
        """Handle network communication in separate thread"""
        while self.running:
            try:
                data = self.socket.recv(1024).decode()
                if not data:
                    break
                    
                messages = data.split('\n')
                for message in messages:
                    if not message:
                        continue
                    try:
                        parsed = json.loads(message)
                        if parsed['type'] == 'game_state':
                            self.game_state = parsed['state']
                        elif parsed['type'] == 'waiting':
                            self.in_queue = True
                            self.queue_position = parsed['position']
                            self.game_state['game_started'] = False
                        elif parsed['type'] == 'game_start':
                            self.in_queue = False
                            self.game_id = parsed['game_id']
                            self.game_state['game_started'] = True
                        elif parsed['type'] == 'error':
                            print("Server error:", parsed['message'])
                            self.running = False
                            break
                    except json.JSONDecodeError:
                        print("Error parsing message:", message)
                        
            except ConnectionResetError:
                print("Lost connection to server")
                self.running = False
                break
                
    def _draw_queue_status(self):
        """Draw the queue status message"""
        messages = []
        if self.in_queue:
            messages.append(f"You are in position {self.queue_position + 1} in the queue")
            messages.append("Waiting for another player...")
        else:
            messages.append("Connecting to server...")
            
        y_offset = self.height // 2 - (len(messages) * 30)
        for message in messages:
            text = self.message_font.render(message, True, self.WHITE)
            text_rect = text.get_rect(center=(self.width//2, y_offset))
            self.screen.blit(text, text_rect)
            y_offset += 60
            
    def _draw_game_id(self):
        """Draw the current game ID"""
        if self.game_id:
            text = self.message_font.render(f"Game: {self.game_id}", True, self.GRAY)
            text_rect = text.get_rect(topleft=(10, 10))
            self.screen.blit(text, text_rect)
            
    def run(self):
        """Main game loop"""
        movement_speed = 5
        
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    
            # Handle continuous keyboard input only when in game
            if self.game_state['game_started']:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_UP]:
                    self._send_movement(-movement_speed)
                elif keys[pygame.K_DOWN]:
                    self._send_movement(movement_speed)
                    
            # Clear screen
            self.screen.fill(self.BLACK)
            
            if not self.game_state['game_started']:
                self._draw_queue_status()
            else:
                # Draw game objects
                self._draw_paddle(50, self.game_state['paddles']['player1']['y'])
                self._draw_paddle(self.width - 50 - self.paddle_width,
                                self.game_state['paddles']['player2']['y'])
                self._draw_ball(self.game_state['ball']['x'],
                              self.game_state['ball']['y'])
                self._draw_scores()
                
            # Always draw game ID if available
            self._draw_game_id()
                
            # Update display
            pygame.display.flip()
            
            # Control frame rate
            self.clock.tick(60)
            
        # Cleanup
        self.socket.close()
        pygame.quit()
        
    def _send_movement(self, movement):
        """Send movement update to server"""
        try:
            message = json.dumps({
                'type': 'move',
                'movement': movement
            })
            self.socket.send(message.encode())
        except (BrokenPipeError, ConnectionResetError):
            self.running = False
            
    def _draw_paddle(self, x, y):
        """Draw a paddle at the specified position"""
        pygame.draw.rect(self.screen, self.WHITE, 
                        (x, y, self.paddle_width, self.paddle_height))
        
    def _draw_ball(self, x, y):
        """Draw the ball at the specified position"""
        pygame.draw.rect(self.screen, self.WHITE,
                        (x, y, self.ball_size, self.ball_size))
        
    def _draw_scores(self):
        """Draw the current scores"""
        # Player 1 score
        score1 = self.score_font.render(
            str(self.game_state['paddles']['player1']['score']), True, self.WHITE)
        self.screen.blit(score1, (self.width//4, 50))
        
        # Player 2 score
        score2 = self.score_font.render(
            str(self.game_state['paddles']['player2']['score']), True, self.WHITE)
        self.screen.blit(score2, (3*self.width//4, 50))