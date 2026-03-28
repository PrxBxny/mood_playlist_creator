from flask import Flask
from flask_cors import CORS

from app.config import get_config, BaseConfig
from app.routes.home import home_bp
from app.routes.users import users_bp
from app.routes.playlist import playlist_bp
from app.services.ai_service import AIService
from app.services.music_service import MusicService
from app.services.playlist_service import PlaylistService


def create_app(config: BaseConfig | None = None) -> Flask:
    app = Flask(__name__)
    cfg = config or get_config()

    app.config.from_object(cfg)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    ai_service = AIService(cfg)
    music_service = MusicService(cfg)
    playlist_service = PlaylistService(
        ai_service=ai_service,
        music_service=music_service
    )
    app.extensions["playlist"] = playlist_service

    app.register_blueprint(home_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(playlist_bp)

    @app.route("/health")
    def health():
        return {"status": "ok"}, 200


    return app