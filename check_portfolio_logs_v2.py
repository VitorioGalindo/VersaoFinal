import re

def check_portfolio_logs():
    try:
        with open('logs/backend.log', 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        portfolio_lines = []
        for line in lines:
            if re.search(r'(portfolio|cota|valor)', line, re.IGNORECASE):
                portfolio_lines.append(line.strip())
                
        # Show last 30 lines
        for line in portfolio_lines[-30:]:
            print(line)
            
    except Exception as e:
        print(f"Error reading logs: {e}")

if __name__ == "__main__":
    check_portfolio_logs()