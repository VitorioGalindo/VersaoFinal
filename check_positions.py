from backend.models import db, PortfolioPosition
from backend.config import Config
from flask import Flask

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    positions = PortfolioPosition.query.filter_by(portfolio_id=1).all()
    print(f'Encontradas {len(positions)} posições:')
    for p in positions:
        print(f'  {p.symbol}: quantity={p.quantity}, avg_price={p.avg_price}, target_weight={p.target_weight}')