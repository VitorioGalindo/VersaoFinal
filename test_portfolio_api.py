import os
import sys
import json
from datetime import date
from backend.routes.portfolio_routes import calculate_portfolio_summary
from backend.routes.portfolio_summary_routes import get_portfolio_summary_data
from backend import create_app

def test_portfolio_api():
    app = create_app()
    with app.test_request_context():
        try:
            print("Testing portfolio summary API endpoint...")
            response = get_portfolio_summary_data(1)
            
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.get_json()}")
        except Exception as e:
            print(f"Error testing portfolio API: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_portfolio_api()