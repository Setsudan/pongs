

from pongClient import PongClient


if __name__ == "__main__":
    HOST = 'localhost'
    PORT = 5000
    
    client = PongClient(HOST, PORT)
    client.run()