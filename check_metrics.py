from backend.models import db, PortfolioEditableMetric
from backend.config import Config
from flask import Flask
from datetime import date

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    today = date.today()
    metrics = PortfolioEditableMetric.query.filter_by(portfolio_id=1, date=today).all()
    print(f'Encontradas {len(metrics)} métricas para {today}:')
    for m in metrics:
        print(f'  {m.metric_key}: {m.metric_value}')
        
    if not metrics:
        print('Nenhuma métrica encontrada para hoje. Buscando data mais recente...')
        latest_metric = PortfolioEditableMetric.query.filter_by(
            portfolio_id=1
        ).order_by(PortfolioEditableMetric.date.desc()).first()
        
        if latest_metric:
            latest_date = latest_metric.date
            print(f'Encontrada data mais recente: {latest_date}')
            metrics = PortfolioEditableMetric.query.filter_by(
                portfolio_id=1, date=latest_date
            ).all()
            print(f'Encontradas {len(metrics)} métricas para {latest_date}:')
            for m in metrics:
                print(f'  {m.metric_key}: {m.metric_value}')
        else:
            print('Nenhuma métrica encontrada no banco de dados')