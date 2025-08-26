# QWEN.md - Project Context for Qwen Code

## Project Overview

This is a comprehensive financial dashboard application with a Flask backend and React/TypeScript frontend. The project provides financial data analysis, real-time market data (with MetaTrader5 integration), company information, portfolio tracking, and AI-powered insights.

### Key Technologies

- **Backend**: Python 3, Flask, SQLAlchemy, PostgreSQL
- **Frontend**: React 19, TypeScript, Vite, Recharts
- **Real-time Data**: MetaTrader5 integration for Brazilian market data
- **AI Services**: Google Gemini API integration
- **Testing**: Pytest for backend, Vitest for frontend
- **Deployment**: Production-ready with Gunicorn

### Architecture

The project follows a monorepo structure with clearly separated backend and frontend components:

```
project/
├── backend/           # Flask application with routes, models, services
├── frontend/          # React/TypeScript dashboard
├── scraper/           # Data collection scripts
├── requirements*.txt  # Python dependencies
├── package.json       # Frontend dependencies (workspace setup)
└── run*.py           # Application startup scripts
```

## Backend Structure

### Core Components

- **Flask Application**: Main app with CORS support, database integration, and route registration
- **Database Models**: Comprehensive financial data models (Company, Ticker, Financial Data, etc.)
- **API Routes**: RESTful endpoints for companies, market data, news, documents, and real-time quotes
- **Services**: Business logic separation with external API integrations
- **Clients**: External service connectors (Bacen, CVM, news sources)

### Key Features

1. **Company Data Management**: Detailed Brazilian company information with financial data
2. **Real-time Market Data**: MetaTrader5 integration for live Brazilian market quotes
3. **Document Processing**: CVM (Brazilian Securities Commission) document handling
4. **AI Integration**: Google Gemini API for intelligent financial insights
5. **Portfolio Tracking**: Personal investment portfolio management
6. **Market Analysis**: Screening tools, historical data, and market overview

## Frontend Structure

### Core Components

- **React Components**: Modular dashboard with specialized financial views
- **State Management**: React hooks for data management and real-time updates
- **Services**: API client integration with typed responses
- **Styling**: Component-based styling with modern UI principles

### Key Features

1. **Dashboard Views**: Portfolio, market news, company overview, historical data
2. **AI Assistant**: Natural language financial analysis and insights
3. **Real-time Data**: WebSocket integration with MetaTrader5 quotes
4. **Data Visualization**: Charts and graphs for financial data analysis
5. **Search & Filter**: Advanced company and ticker search capabilities

## Building and Running

### Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL database
- MetaTrader5 account (optional, for real-time data)

### Backend Setup

1. Install main dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Install optional dependencies:
   ```bash
   # For MetaTrader5 integration
   pip install -r requirements-mt5.txt
   
   # For development and testing
   pip install -r requirements-dev.txt
   ```

3. Install Playwright for web scraping:
   ```bash
   playwright install
   ```

4. Set up environment variables:
   ```bash
   cp backend/.env.example backend/.env
   ```
   Edit `backend/.env` with database credentials, API keys, and other configurations.

### Frontend Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Set up environment variables:
   ```bash
   cp frontend/.env.example frontend/.env
   ```
   Update with API URLs and Google Gemini key.

### Database Migrations

After any model changes, generate and apply migrations:
```bash
flask db migrate -m "description"
flask db upgrade
```

Or with Alembic directly:
```bash
alembic upgrade head
```

### Running the Application

Start the backend (terminal 1):
```bash
python run_backend.py
```

Start the frontend (terminal 2):
```bash
npm run dev
```

The dashboard will be available at `http://localhost:3000` and APIs at `http://localhost:5001/api`.

## Testing

### Backend Testing

Run all tests:
```bash
pytest -q
```

Run specific test files:
```bash
pytest test_company_news_routes.py -v
```

For MetaTrader5 tests, set environment variables first:
```bash
export MT5_LOGIN=your_login
export MT5_PASSWORD=your_password
export MT5_SERVER=your_server
pytest -q test_cotacoes_mt5.py
```

### Frontend Testing

Run frontend tests:
```bash
npm test
```

## Development Conventions

### Backend

1. **Code Structure**: 
   - Routes are separated by domain (companies, market, news, etc.)
   - Services encapsulate business logic
   - Models follow SQLAlchemy conventions
   - Error handling with proper logging

2. **Database**: 
   - PostgreSQL with SQLAlchemy ORM
   - Alembic for migrations
   - Environment-based configuration

3. **API Design**:
   - RESTful endpoints with JSON responses
   - Consistent response format with status fields
   - Proper error codes and messages

### Frontend

1. **Component Structure**:
   - Reusable components in the components/ directory
   - TypeScript typing for all props and state
   - Component-based styling

2. **State Management**:
   - React hooks for local state
   - Custom hooks for complex logic
   - Context API for global state when needed

3. **API Integration**:
   - Centralized service layer
   - Typed API responses
   - Error handling and loading states

## Key Environment Variables

### Backend (.env)
```
DB_HOST=localhost
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=your_database
GEMINI_API_KEY=your_google_gemini_key
SECRET_KEY=your_secret_key
```

### Frontend (.env)
```
VITE_API_BASE_URL=http://localhost:5001/api
VITE_GEMINI_API_KEY=your_google_gemini_key
```

## Special Features

### MetaTrader5 Integration
- Real-time Brazilian market data
- WebSocket-based streaming
- Fallback simulation mode
- Market status detection

### AI Features
- Google Gemini integration for financial insights
- Natural language processing of financial documents
- Automated analysis and summarization

### Data Sources
- CVM (Brazilian Securities Commission) documents
- Bacen (Brazilian Central Bank) data
- Company financial statements
- Market news and sentiment analysis

## Health Checks

Verify backend status:
```bash
curl http://localhost:5001/health
curl http://localhost:5001/api/health
```

Check CVM document types:
```bash
curl http://localhost:5001/api/cvm/document-types
```