"""Run the local monitoring server with Waitress, including offline detection."""
import logging

from waitress import serve

from app import create_app
from services.monitoring import start_monitor


def main():
    logging.basicConfig(level=logging.INFO)
    application = create_app()
    stopped, worker = start_monitor(application)
    try:
        serve(application, host=application.config["SERVER_HOST"],
              port=application.config["SERVER_PORT"], threads=4)
    finally:
        stopped.set()
        worker.join(timeout=6)


if __name__ == "__main__":
    main()
