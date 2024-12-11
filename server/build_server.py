from PyInstaller.__main__ import run

if __name__ == '__main__':
    opts = [
        'main.py',                    # Your main script
        '--onefile',                  # Create a single executable
        '--name=PongServer',          # Name of your executable
        '--clean',                    # Clean PyInstaller cache and remove temporary files
        '--add-data=server:server',   # Include the server package
    ]
    run(opts)