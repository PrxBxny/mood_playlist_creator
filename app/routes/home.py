from flask import Blueprint, jsonify, render_template

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def index():
    return render_template("index.html")

@home_bp.route("/ping")
def ping():
    return jsonify({"message": "home router is alive"}), 200