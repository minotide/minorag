from minorag.config import WEB_PORT
from minorag.web import app

if __name__ == "__main__":
    print(f"minorag iniciado em http://localhost:{WEB_PORT}")
    app.run(host="0.0.0.0", port=WEB_PORT, debug=False)
