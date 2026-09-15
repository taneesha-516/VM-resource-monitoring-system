"""Run the teaching server with: python app.py."""
import math
import sqlite3

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from config import Config
from models.db import close_db, init_db


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    for setting in ("METRIC_INTERVAL", "OFFLINE_TIMEOUT"):
        if not math.isfinite(app.config[setting]) or app.config[setting] <= 0:
            raise ValueError(f"{setting} must be positive.")
    for setting in ("CPU_THRESHOLD", "MEMORY_THRESHOLD", "DISK_THRESHOLD"):
        if not 0 <= app.config[setting] <= 100:
            raise ValueError(f"{setting} must be between 0 and 100.")
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()
    from routes.api import api
    app.register_blueprint(api)
    from routes.views import views
    app.register_blueprint(views)

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(error=error.description), error.code

    @app.errorhandler(sqlite3.Error)
    def database_error(error):
        app.logger.exception("Database operation failed")
        return jsonify(error="Database is unavailable; please retry."), 503

    return app


if __name__ == "__main__":
    from services.monitoring import start_monitor

    application = create_app()
    stopped, worker = start_monitor(application)
    try:
        application.run(
            host=application.config["SERVER_HOST"],
            port=application.config["SERVER_PORT"],
            debug=False,
            use_reloader=False,
        )
    finally:
        stopped.set()
        worker.join(timeout=6)
