import os
import sys
from datetime import date
from backend.models import db, PortfolioEditableMetric
from backend import create_app

def check_portfolio_metrics():
    app = create_app()
    with app.app_context():
        # Check if there are any editable metrics for portfolio 1
        metrics = PortfolioEditableMetric.query.filter_by(portfolio_id=1).all()
        
        if not metrics:
            print("No editable metrics found for portfolio 1")
            return
            
        print(f"Found {len(metrics)} editable metrics for portfolio 1:")
        for metric in metrics:
            print(f"  {metric.metric_key}: {metric.metric_value} (date: {metric.date})")
            
        # Check for today's metrics specifically
        today = date.today()
        today_metrics = PortfolioEditableMetric.query.filter_by(
            portfolio_id=1, date=today
        ).all()
        
        if today_metrics:
            print(f"\nToday's metrics ({today}):")
            for metric in today_metrics:
                print(f"  {metric.metric_key}: {metric.metric_value}")
        else:
            print(f"\nNo metrics found for today ({today})")

if __name__ == "__main__":
    check_portfolio_metrics()