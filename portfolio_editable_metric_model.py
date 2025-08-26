# Adicione este código ao final do arquivo models.py, antes da última classe

class PortfolioEditableMetric(db.Model):
    __tablename__ = 'portfolio_editable_metrics'

    id = db.Column(Integer, primary_key=True)
    portfolio_id = db.Column(Integer, ForeignKey('portfolios.id'), nullable=False, index=True)
    metric_key = db.Column(String(100), nullable=False)
    metric_value = db.Column(Numeric(20, 4), nullable=False)
    date = db.Column(Date, nullable=False, server_default=func.current_date())
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(DateTime(timezone=True), onupdate=func.now())

    portfolio = relationship("Portfolio", back_populates="editable_metrics")

    __table_args__ = (
        db.UniqueConstraint('portfolio_id', 'metric_key', 'date', name='uix_portfolio_editable_metric_date'),
    )