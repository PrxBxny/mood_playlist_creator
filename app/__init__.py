from flask import Flask
from flask_cors import CORS

from app.config import get_config, BaseConfig
from app.routes.home import home_bp
from app.routes.users import users_bp
from app.routes.playlist import playlist_bp


def create_app(config: BaseConfig | None = None) -> Flask:

    app = Flask(__name__)
    cfg = config or get_config()

    app.config.from_object(cfg)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    app.register_blueprint(home_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(playlist_bp)

    @app.route("/health")
    def health():
        return {"status": "ok"}, 200


    return app