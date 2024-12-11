import pygame
import socket
import json
import threading
import sys

class PongClient:
    """
        Initialise une nouvelle instance du jeu Pong multijoueur.
        Args:
            host (str): L'adresse hôte du serveur. Par défaut 'localhost'.
            port (int): Le port du serveur. Par défaut 5000.
        Attributs:
            width (int): La largeur de la fenêtre de jeu.
            height (int): La hauteur de la fenêtre de jeu.
            screen (pygame.Surface): La surface de la fenêtre de jeu.
            paddle_height (int): La hauteur des raquettes.
            paddle_width (int): La largeur des raquettes.
            ball_size (int): La taille de la balle.
            WHITE (tuple): La couleur blanche en RGB.
            BLACK (tuple): La couleur noire en RGB.
            game_state (dict): L'état actuel du jeu, incluant les positions des raquettes et de la balle, et les scores.
            socket (socket.socket): Le socket réseau pour la communication avec le serveur.
            running (bool): Indicateur de l'état de fonctionnement du thread réseau.
            network_thread (threading.Thread): Le thread gérant la communication réseau.
            font (pygame.font.Font): La police utilisée pour afficher les scores.
            clock (pygame.time.Clock): L'horloge pour contrôler le taux de rafraîchissement des images.
        Exceptions:
            ConnectionRefusedError: Si la connexion au serveur échoue.
        """
    def __init__(self, host='localhost', port=5000):
        # Initialize Pygame
        pygame.init()
        self.width = 800
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Multiplayer Pong")
        
        # Game objects dimensions
        self.paddle_height = 60
        self.paddle_width = 10
        self.ball_size = 10
        
        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        
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
        
        # Font for scoring
        self.font = pygame.font.Font(None, 74)
        
        # Clock for controlling frame rate
        self.clock = pygame.time.Clock()
        
    def _handle_network(self):
        """
        Gère la communication réseau dans un thread séparé.
        Tant que l'attribut `self.running` est vrai, cette méthode essaie de recevoir des données du socket.
        Les données reçues sont décodées et divisées en messages individuels.
        Chaque message est ensuite analysé et traité en fonction de son type.
        Types de messages traités :
        - 'game_state' : Met à jour l'état du jeu avec les données reçues.
        - 'error' : Affiche un message d'erreur et arrête l'exécution.
        En cas d'erreur de connexion ou de déconnexion du serveur, la méthode arrête l'exécution.
        Exceptions gérées :
        - ConnectionResetError : Perte de connexion avec le serveur.
        - json.JSONDecodeError : Erreur lors de l'analyse d'un message JSON.
        """
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
        score1 = self.font.render(
            str(self.game_state['paddles']['player1']['score']), True, self.WHITE)
        self.screen.blit(score1, (self.width//4, 50))
        
        # Player 2 score
        score2 = self.font.render(
            str(self.game_state['paddles']['player2']['score']), True, self.WHITE)
        self.screen.blit(score2, (3*self.width//4, 50))
        
    def _draw_waiting_message(self):
        """Draw waiting for players message"""
        font = pygame.font.Font(None, 36)
        text = font.render("Waiting for players...", True, self.WHITE)
        text_rect = text.get_rect(center=(self.width//2, self.height//2))
        self.screen.blit(text, text_rect)
        
    def run(self):
        """Main game loop"""
        movement_speed = 5
        
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    
            # Handle continuous keyboard input
            keys = pygame.key.get_pressed()
            if keys[pygame.K_UP]:
                self._send_movement(-movement_speed)
            elif keys[pygame.K_DOWN]:
                self._send_movement(movement_speed)
                
            # Clear screen
            self.screen.fill(self.BLACK)
            
            if not self.game_state['game_started']:
                self._draw_waiting_message()
            else:
                # Draw game objects
                # Left paddle (Player 1)
                self._draw_paddle(50, self.game_state['paddles']['player1']['y'])
                
                # Right paddle (Player 2)
                self._draw_paddle(self.width - 50 - self.paddle_width,
                                self.game_state['paddles']['player2']['y'])
                
                # Ball
                self._draw_ball(self.game_state['ball']['x'],
                              self.game_state['ball']['y'])
                
                # Scores
                self._draw_scores()
                
            # Update display
            pygame.display.flip()
            
            # Control frame rate
            self.clock.tick(60)
            
        # Cleanup
        self.socket.close()
        pygame.quit()

