import os
import sys
from datetime import date
from backend.models import db, PortfolioPosition, Portfolio, AssetMetrics
from backend import create_app

def check_asset_metrics():
    app = create_app()
    with app.app_context():
        # Get positions for portfolio 1
        positions = PortfolioPosition.query.filter_by(portfolio_id=1).all()
        
        if not positions:
            print("No positions found for portfolio 1")
            return
            
        print(f"Checking asset metrics for {len(positions)} positions:")
        for pos in positions:
            # Check if there are asset metrics for this symbol
            metrics = AssetMetrics.query.filter_by(symbol=pos.symbol).first()
            
            if not metrics:
                print(f"  {pos.symbol}: No metrics found")
            else:
                print(f"  {pos.symbol}: last_price={metrics.last_price}, previous_close={metrics.previous_close}")

if __name__ == "__main__":
    check_asset_metrics()