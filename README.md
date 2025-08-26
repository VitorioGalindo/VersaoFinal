# Dashboard Financeiro – Projeto Final

Este repositório contém o backend em Flask e o frontend em React/TypeScript.

## Instalação

### Backend
Instale as dependências principais:
```bash
pip install -r requirements.txt
```

Dependências opcionais:

- **Integração MetaTrader5**
  ```bash
  pip install -r requirements-mt5.txt
  ```
- **Desenvolvimento e testes**
  ```bash
pip install -r requirements-dev.txt
```

Após a instalação, execute:
```bash
playwright install
```

### Migrações de Banco de Dados
Após qualquer alteração nos modelos, gere e aplique as migrações:
```bash
flask db migrate -m "mensagem"
flask db upgrade
```
Para aplicar todas as migrações pendentes diretamente via Alembic:
```bash
alembic upgrade head
```

### Frontend
```bash
npm install
```

### Scraper
```bash
pip install -r requirements.txt
cd scraper
python app.py
```

## Variáveis de Ambiente

Crie arquivos `.env` a partir dos modelos de exemplo e preencha com suas credenciais:

### Backend
```bash
cp backend/.env.example backend/.env
```
Edite `backend/.env` com as configurações do banco, chave da API do Google Gemini e demais valores necessários.

### Frontend
```bash
cp frontend/.env.example frontend/.env
```
Atualize `frontend/.env` com as URLs da API e a chave do Gemini antes de iniciar o projeto.

### Scraper
Crie um arquivo `.env` na raiz do projeto com as credenciais do banco utilizadas pelo scraper:
```bash
cat <<EOF > .env
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nome_do_banco
EOF
```

### Recursos de IA (Google Gemini)

Os recursos de inteligência artificial utilizam a API do Google Gemini. Defina `GEMINI_API_KEY` no `.env` do backend e `VITE_GEMINI_API_KEY` no `.env` do frontend.

Caso essa chave não seja fornecida, o sistema continuará funcionando, mas o `geminiService` registrará um `console.warn` e retornará mensagens de fallback em vez de respostas geradas.

### Sistema de Logs e Alertas

O backend grava erros em arquivo e pode enviar exceções para serviços externos como o Sentry. As principais variáveis de ambiente são:

```bash
# Caminho do arquivo de log (padrão: logs/backend.log)
export LOG_FILE=/caminho/para/backend.log

# Nível de log (padrão: INFO)
export LOG_LEVEL=DEBUG

# DSN do Sentry para captura de exceções (opcional)
export SENTRY_DSN=https://exemplo@sentry.io/123
```

Com `LOG_FILE` definido, todas as exceções — incluindo erros de banco de dados capturados pelo SQLAlchemy — serão registradas no arquivo especificado. Caso `SENTRY_DSN` esteja configurado e o pacote `sentry-sdk` instalado, as exceções também serão enviadas ao Sentry para monitoramento.

## Executar Testes

Backend:
```bash
pytest -q
```

### Testes com MetaTrader5

Alguns testes dependem de credenciais do MetaTrader5. Defina as variáveis de ambiente antes de executá-los:

```bash
export MT5_LOGIN=seu_login
export MT5_PASSWORD=sua_senha
export MT5_SERVER=seu_servidor
pytest -q test_cotacoes_mt5.py
```

Frontend:
```bash
npm test
```

## Subir o Projeto

Backend (terminal 1):
```bash
python run_backend.py
```
Ao iniciar por esse comando, as migrações do banco de dados são aplicadas automaticamente,
garantindo que o schema esteja sempre atualizado.

Frontend (terminal 2):
```bash
npm run dev
```

O dashboard estará disponível em `http://localhost:3000` e as APIs em `http://localhost:5001/api`.

### Health checks

Verifique rapidamente se o backend está no ar:

```bash
curl http://localhost:5001/health
curl http://localhost:5001/api/health
```

### Exemplo de rota CVM

Para listar os tipos de documentos disponíveis:

```bash
curl http://localhost:5001/api/cvm/document-types
```

Resposta:

```json
{
  "success": true,
  "document_types": ["DFP", "ITR", "..."]
}
```

No dashboard, o filtro "Período de Publicação" dos Documentos CVM utiliza dois campos `input` do tipo `date` (início e fim) no formato `YYYY-MM-DD` para definir o intervalo desejado.

## Documentação Avançada

Detalhes sobre a integração MetaTrader5 estão em [INTEGRACAO_METATRADER5.md](INTEGRACAO_METATRADER5.md).
