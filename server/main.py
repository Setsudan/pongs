from server.server import PongServer


if __name__ == '__main__':
    server = PongServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")