import os
import sys
from datetime import date
from backend.models import db, AssetMetrics
from backend import create_app

def check_previous_close():
    app = create_app()
    with app.app_context():
        # Check a few symbols
        symbols = ['VALE3', 'PETR4', 'ITUB4', 'BOVA11']
        for symbol in symbols:
            metrics = AssetMetrics.query.filter_by(symbol=symbol).first()
            if metrics:
                print(f"{symbol}: previous_close={metrics.previous_close}, previous_close_correct={metrics.previous_close_correct}")
            else:
                print(f"{symbol}: No metrics found")

if __name__ == "__main__":
    check_previous_close()