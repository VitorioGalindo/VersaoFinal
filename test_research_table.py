import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Carregar variáveis de ambiente
load_dotenv()

from backend import create_app
from backend.models import ResearchNote

def test_research_table():
    app = create_app()
    with app.app_context():
        try:
            # Testar se a tabela existe e podemos fazer consultas
            count = ResearchNote.query.count()
            print(f"Total de notas na tabela: {count}")
            
            # Tentar criar uma nota de teste
            note = ResearchNote(title="Teste", content="Conteúdo de teste")
            from backend.models import db
            db.session.add(note)
            db.session.commit()
            print(f"Nota de teste criada com ID: {note.id}")
            
            # Limpar a nota de teste
            db.session.delete(note)
            db.session.commit()
            print("Nota de teste removida")
            
        except Exception as e:
            print(f"Erro ao acessar a tabela research_notes: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_research_table()