import logging

from backend import socketio
from backend.services.metatrader5_rtd_worker import initialize_rtd_worker

logger = logging.getLogger(__name__)


def integrate_rtd_worker(app):
    """Integrate Socket.IO and the RTD worker with the Flask app.

    Returns a tuple ``(socketio, rtd_worker)`` when the worker starts
    successfully; otherwise ``(None, None)``.
    """
    try:
        rtd_worker = initialize_rtd_worker(socketio)
        app.socketio = socketio
        app.rtd_worker = rtd_worker
        app.mt5_worker = rtd_worker  # backward compatibility
        return socketio, rtd_worker
    except Exception as e:  # pragma: no cover - defensive
        logger.warning(f"RTD worker integration failed: {e}")
        app.socketio = None
        app.rtd_worker = None
        app.mt5_worker = None
        return None, None
