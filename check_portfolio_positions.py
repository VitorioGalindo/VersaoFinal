import os
import sys
from datetime import date
from backend.models import db, PortfolioPosition, Portfolio
from backend import create_app

def check_portfolio_positions():
    app = create_app()
    with app.app_context():
        # Check if portfolio 1 exists
        portfolio = Portfolio.query.get(1)
        if not portfolio:
            print("Portfolio 1 does not exist")
            return
            
        print(f"Portfolio 1 exists: {portfolio.name}")
            
        # Check if there are any positions for portfolio 1
        positions = PortfolioPosition.query.filter_by(portfolio_id=1).all()
        
        if not positions:
            print("No positions found for portfolio 1")
            return
            
        print(f"Found {len(positions)} positions for portfolio 1:")
        for pos in positions:
            print(f"  {pos.symbol}: quantity={pos.quantity}, avg_price={pos.avg_price}")

if __name__ == "__main__":
    check_portfolio_positions()