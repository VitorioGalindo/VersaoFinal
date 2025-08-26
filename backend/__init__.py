from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_migrate import Migrate
from sqlalchemy import text
from .config import Config
import logging
import os
import sys


def setup_logging():
    """Configure logging for the application.

    Creates a file handler and integrates with Sentry (if available).
    """
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_file = os.environ.get("LOG_FILE", "logs/backend.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)

    # Ensure SQLAlchemy errors are also captured
    sqlalchemy_logger = logging.getLogger("sqlalchemy")
    sqlalchemy_logger.setLevel(logging.ERROR)

    sentry_dsn = os.environ.get("SENTRY_DSN")
    if sentry_dsn:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.flask import FlaskIntegration
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

            sentry_sdk.init(
                dsn=sentry_dsn,
                integrations=[FlaskIntegration(), SqlalchemyIntegration()],
            )
        except ImportError:
            root_logger.warning(
                "sentry-sdk não instalado. Ignorando integração com Sentry."
            )

db = SQLAlchemy()
socketio = SocketIO()
migrate = Migrate()

def create_app():
    setup_logging()

    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*")

    @app.route("/health")
    def health_check():
        return jsonify({"status": "ok"}), 200

    @app.route("/api/health")
    def api_health_check():
        try:
            db.session.execute(text("SELECT 1"))
            db_status = "connected"
        except Exception:
            db_status = "disconnected"
        return jsonify({"status": "ok", "database": db_status}), 200

    with app.app_context():
        # --- REGISTRO DE TODOS OS BLUEPRINTS ---
        from .routes.companies_routes import companies_bp
        from .routes.tickers_routes import tickers_bp
        from .routes.market_routes import market_bp
        from .routes.historical_routes import historical_bp
        from .routes.ai_routes import ai_bp
        from .routes.realtime_routes import realtime_bp
        from .routes.financials_routes import financials_bp
        from .routes.documents_routes import documents_bp, cvm_bp
        from .routes.portfolio_routes import portfolio_bp
        from .routes.portfolio_summary_routes import portfolio_summary_bp
        from .routes.screening_routes import screening_bp
        from .routes.search_routes import search_bp
        from .routes.macro_routes import macro_bp
        from .routes.news_routes import news_bp
        from .routes.research_routes import research_bp
        from .routes.company_news_routes import company_news_bp


        app.register_blueprint(companies_bp, url_prefix='/api/companies')
        app.register_blueprint(tickers_bp, url_prefix='/api/tickers')
        app.register_blueprint(market_bp, url_prefix='/api/market')
        app.register_blueprint(historical_bp, url_prefix='/api/historical')
        app.register_blueprint(ai_bp, url_prefix='/api/ai')
        app.register_blueprint(realtime_bp, url_prefix='/api/realtime')
        app.register_blueprint(financials_bp, url_prefix='/api/financials')
        app.register_blueprint(documents_bp, url_prefix='/api/documents')
        app.register_blueprint(cvm_bp, url_prefix='/api/cvm')
        app.register_blueprint(portfolio_bp, url_prefix='/api/portfolio')
        app.register_blueprint(portfolio_summary_bp, url_prefix='/api/portfolio-summary')
        app.register_blueprint(screening_bp, url_prefix='/api/screening')
        app.register_blueprint(search_bp, url_prefix='/api/search')
        app.register_blueprint(macro_bp, url_prefix='/api/macro')
        app.register_blueprint(news_bp, url_prefix='/api/news')
        app.register_blueprint(research_bp, url_prefix='/api/research')
        app.register_blueprint(company_news_bp, url_prefix='/api/company-news')


    return app
