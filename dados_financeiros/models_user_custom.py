# models_user_custom.py - Versão final e completa, sincronizada com models.py

from sqlalchemy import (Column, Integer, String, Date, Boolean, ForeignKey, 
                        BigInteger, DateTime)
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Company(Base):
    """
    Modelo para a tabela 'companies'.
    """
    __tablename__ = 'companies'

    id = Column(Integer, primary_key=True)
    cnpj = Column(String(14), unique=True, nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    cvm_code = Column(String(10), unique=True, index=True)

    financial_data = relationship("CvmDocument", back_populates="company")
    
    def to_dict(self):
        return {
            'id': self.id,
            'cnpj': self.cnpj,
            'company_name': self.company_name,
            'cvm_code': self.cvm_code
        }


class CvmDocument(Base):
    """
    Modelo para a tabela 'cvm_financial_data'.
    """
    __tablename__ = 'cvm_financial_data'

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    reference_date = Column(Date, nullable=False, index=True)
    report_type = Column(String(10), nullable=False)
    report_version = Column(String(20), nullable=False)
    
    # --- Coluna adicionada para sincronia ---
    cvm_version = Column(String(50))
    
    account_code = Column(String(50), nullable=False, index=True)
    account_name = Column(String(255))
    account_value = Column(BigInteger, nullable=False)
    currency = Column(String(50))
    is_fixed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company", back_populates="financial_data")

    def to_dict(self):
        """Converte o objeto CvmDocument para um dicionário."""
        return {
            'id': self.id,
            'company_id': self.company_id,
            'reference_date': self.reference_date.isoformat() if self.reference_date else None,
            'report_type': self.report_type,
            'report_version': self.report_version,
            'cvm_version': self.cvm_version,
            'account_code': self.account_code,
            'account_name': self.account_name,
            'account_value': self.account_value,
            'currency': self.currency,
            'is_fixed': self.is_fixed,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }