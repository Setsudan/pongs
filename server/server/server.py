import json
import socket
import threading
import time

from server.game import GamePool


class PongServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen(10)  # Increased backlog for multiple connections
        
        self.pool = GamePool()
        self.lock = threading.Lock()
        
        print(f"Server started on {host}:{port}")
        
    def start(self):
        """Start the game server"""
        # Start game update loop in separate thread
        update_thread = threading.Thread(target=self._game_loop)
        update_thread.daemon = True
        update_thread.start()
        
        # Accept client connections
        while True:
            client_socket, address = self.server_socket.accept()
            print(f"Client connected from {address}")
            
            # Start client handler thread
            client_thread = threading.Thread(target=self._handle_client, args=(client_socket,))
            client_thread.daemon = True
            client_thread.start()
            
    def _handle_client(self, client_socket):
        """Handle individual client connection"""
        try:
            # Add player to pool
            with self.lock:
                self.pool.add_player(None, client_socket)
            
            while True:
                data = client_socket.recv(1024).decode()
                if not data:
                    break
                    
                message = json.loads(data)
                
                with self.lock:
                    game = self.pool.get_game_for_player(client_socket)
                    if game and message['type'] == 'move':
                        player_role = self.pool.get_player_role(client_socket)
                        game.update_paddle(player_role, message['movement'])
                        
        except (ConnectionResetError, json.JSONDecodeError):
            pass
        finally:
            # Clean up disconnected client
            with self.lock:
                self.pool.remove_player(client_socket)
            client_socket.close()
            
    def _game_loop(self):
        """Main game update loop"""
        while True:
            with self.lock:
                # Update all active games
                for game_info in self.pool.active_games.values():
                    game = game_info['game']
                    game.update_ball()
                    
                    # Broadcast state to both players
                    state_message = {
                        'type': 'game_state',
                        'state': game.get_state()
                    }
                    
                    data = json.dumps(state_message).encode()
                    for player_socket in game_info['players'].values():
                        try:
                            player_socket.send(data)
                        except (BrokenPipeError, ConnectionResetError):
                            self.pool.remove_player(player_socket)
                            
            time.sleep(1/60)  # 60 FPS