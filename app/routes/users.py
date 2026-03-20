from flask import Blueprint, jsonify

from app.services.user_service import get_users

users_bp = Blueprint("user", __name__, url_prefix="/users")


@users_bp.route("/ping")
def ping():
    return jsonify({"message": "users router is alive"}), 200

@users_bp.route("/get_users")
def get_stats():
    users = get_users()
    return jsonify([user.model_dump() for user in users])