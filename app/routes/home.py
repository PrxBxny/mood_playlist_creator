from flask import Blueprint, jsonify

home_bp = Blueprint("home", __name__)


@home_bp.route("/ping")
def ping():
    return jsonify({"message": "home router is alive"}), 200