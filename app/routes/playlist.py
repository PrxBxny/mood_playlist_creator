from flask import Blueprint, jsonify

playlist_bp = Blueprint("playlist", __name__, url_prefix="/playlist")


@playlist_bp.route("/ping")
def ping():
    return jsonify({"message": "playlist router is alive"}), 200