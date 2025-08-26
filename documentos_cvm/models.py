# models.py
from sqlalchemy import Column, Integer, String, DateTime, Text, BigInteger, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class Company(Base):
    __tablename__ = 'companies'

    id = Column(Integer, primary_key=True)
    cnpj = Column('cnpj', String(20), unique=True, nullable=False)
    
    # LINHA ADICIONADA: Mapeia a coluna 'cvm_code' do banco de dados
    cvm_code = Column('cvm_code', Integer, index=True) 
    
    documents = relationship("CvmDocument", back_populates="company")

class CvmDocument(Base):
    __tablename__ = 'cvm_documents'

    id = Column(BigInteger, primary_key=True)
    
    # Chave estrangeira para a tabela 'companies'
    company_id = Column('company_id', Integer, ForeignKey('companies.id'), nullable=False)
    
    cvm_code = Column('cvm_code', Integer)
    document_type = Column('document_type', String(100))
    document_category = Column('document_category', String(200))
    title = Column('title', String(500))
    delivery_date = Column('delivery_date', DateTime)
    reference_date = Column('reference_date', DateTime)
    download_url = Column('download_url', String(1000), unique=True, nullable=False)
    status = Column('status', String(50), default='PENDING_DOWNLOAD')
    processing_status = Column('processing_status', String(50), default='NOT_PROCESSED')
    created_at = Column('created_at', DateTime, server_default=func.now())

    company = relationship("Company", back_populates="documents")

    def __repr__(self):
        return f"<CvmDocument(company_id='{self.company_id}', title='{self.title}')>"
