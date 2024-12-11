import json
import socket
import threading
import time

from server.game import PongGame


class PongServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen(2)
        
        self.clients = {}
        self.game = PongGame()
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
            if len(self.clients) >= 2:
                client_socket.send(json.dumps({'type': 'error', 'message': 'Game is full'}).encode())
                client_socket.close()
                continue
                
            # Assign player number
            player_id = 'player1' if 'player1' not in self.clients else 'player2'
            self.clients[player_id] = client_socket
            
            # Start client handler thread
            client_thread = threading.Thread(target=self._handle_client, args=(client_socket, player_id))
            client_thread.daemon = True
            client_thread.start()
            
            print(f"Client connected from {address} as {player_id}")
            
            # Start game when both players connected
            if len(self.clients) == 2:
                self.game.game_started = True
                self._broadcast({'type': 'game_start'})
                
    def _handle_client(self, client_socket, player_id):
        """Handle individual client connection"""
        try:
            while True:
                data = client_socket.recv(1024).decode()
                if not data:
                    break
                    
                message = json.loads(data)
                
                with self.lock:
                    if message['type'] == 'move':
                        self.game.update_paddle(player_id, message['movement'])
                        
        except (ConnectionResetError, json.JSONDecodeError):
            pass
        finally:
            # Clean up disconnected client
            with self.lock:
                if player_id in self.clients:
                    del self.clients[player_id]
                self.game.game_started = False
                print(f"{player_id} disconnected")
                
            client_socket.close()
            
    def _game_loop(self):
        """Main game update loop"""
        while True:
            with self.lock:
                self.game.update_ball()
                self._broadcast({
                    'type': 'game_state',
                    'state': self.game.get_state()
                })
            time.sleep(1/60)  # 60 FPS
            
    def _broadcast(self, message):
        """Send message to all connected clients"""
        data = json.dumps(message).encode()
        disconnected = []
        
        for player_id, client in self.clients.items():
            try:
                client.send(data)
            except (BrokenPipeError, ConnectionResetError):
                disconnected.append(player_id)
                
        # Clean up disconnected clients
        for player_id in disconnected:
            if player_id in self.clients:
                del self.clients[player_id]
