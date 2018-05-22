import os
from app import create_app

def run_app(host='127.0.0.1', port=5000):
    flask_config = os.environ[ 'FLASK_CONFIG' ] or 'development'
    app = create_app(flask_config)
    return app.run( host=host, port=port)

if __name__ == "__main__":
    run_app()
