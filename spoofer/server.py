"""Local-only web UI for setting the iPhone's location."""

from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from spoofer.device import LocationController, LocationError

HOST = "127.0.0.1"
PORT = 5055
STATIC_DIR = Path(__file__).parent / "static"


def create_app(controller: LocationController) -> Flask:
    app = Flask(__name__)

    def status_payload():
        loc = controller.current
        return {"spoofing": loc is not None,
                "lat": loc.lat if loc else None,
                "lon": loc.lon if loc else None}

    @app.get("/")
    def index():
        return send_from_directory(STATIC_DIR, "index.html")

    @app.get("/status")
    def status():
        return jsonify(ok=True, data=status_payload(), error=None)

    @app.post("/location")
    def set_location():
        body = request.get_json(silent=True) or {}
        try:
            controller.set_location(body.get("lat"), body.get("lon"))
        except LocationError as exc:
            return jsonify(ok=False, data=status_payload(), error=str(exc)), 400
        return jsonify(ok=True, data=status_payload(), error=None)

    @app.post("/clear")
    def clear():
        try:
            controller.clear()
        except LocationError as exc:
            return jsonify(ok=False, data=status_payload(), error=str(exc)), 400
        return jsonify(ok=True, data=status_payload(), error=None)

    return app


if __name__ == "__main__":
    create_app(LocationController()).run(host=HOST, port=PORT)
