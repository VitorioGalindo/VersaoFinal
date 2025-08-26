import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.models import CvmDocument

# Obter colunas do modelo
model_columns = [column.name for column in CvmDocument.__table__.columns]
print("Colunas no modelo CvmDocument:")
for col in model_columns:
    print(f"- {col}")