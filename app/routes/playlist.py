from flask import Blueprint, request, jsonify
from pydantic import ValidationError

from app.models.schemas import PlaylistRequest
from app.utils.exceptions import MoodifyError

playlist_bp = Blueprint("playlist", __name__, url_prefix="/playlist")


@playlist_bp.route("/ping")
def ping():
    return jsonify({"message": "playlist router is alive"}), 200

@playlist_bp.route("/generate", methods=["POST"])
def generate():
    try:
        #.model_validate - сразу сопоставление json с моделью, может выкинуть ValidationError
        data = PlaylistRequest.model_validate(request.get_json(silent=True) or {})

        # result = playlist_service.generate(data):
            # tags = передать data в ai и получить теги
            # playlist = передать теги в lastfm и получить плейлист
            # return json список с плейлистом и треками

        # return jsonify(result.model_dump()), 200

        return jsonify({"заглушка": "rarrrr"}), 200


    except ValidationError as e:
        # ошибка клиента 400 - неверные данные
        return jsonify({"error": "Невалидный запрос", "detail": e.errors()}), 400

    except MoodifyError as e:
        # наша внутренняя ошибка
        return jsonify({"error": str(e)}), 500

    except Exception as e:
        # "предохранитель" на случай непредвиденных падений
        return jsonify({"error": f"Unknown server error: {str(e)}"}), 500