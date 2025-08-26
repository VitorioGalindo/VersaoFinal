import os
from docx import Document

def test_docx_reading():
    # Caminho para o arquivo de template
    template_path = os.path.join('frameworks', 'acoes-ronan.docx')
    print(f"Caminho do template: {template_path}")
    print(f"Caminho absoluto: {os.path.abspath(template_path)}")
    print(f"Arquivo existe: {os.path.exists(template_path)}")
    
    if os.path.exists(template_path):
        try:
            # Ler o documento .docx
            doc = Document(template_path)
            print("Documento lido com sucesso")
            
            # Converter o conteúdo do documento para texto
            full_text = []
            for i, paragraph in enumerate(doc.paragraphs):
                full_text.append(paragraph.text)
                if i < 5:  # Mostrar apenas os primeiros 5 parágrafos
                    print(f"Parágrafo {i}: {paragraph.text}")
            
            framework = '\n'.join(full_text)
            print("Conteúdo do framework:")
            print("-" * 50)
            print(framework[:500])  # Mostrar apenas os primeiros 500 caracteres
            print("-" * 50)
            
        except Exception as e:
            print(f"Erro ao ler o documento: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Arquivo não encontrado")

if __name__ == "__main__":
    test_docx_reading()