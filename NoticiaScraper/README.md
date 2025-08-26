# 🇧🇷 Sistema de Scraping Financeiro Brasileiro

Sistema automatizado para coleta contínua de notícias financeiras de 9 portais brasileiros principais.

## 📊 Portais Ativos

- **G1 Economia** - Notícias gerais e econômicas
- **Brazil Journal** - Análises empresariais e mercado
- **Valor Econômico** - Notícias financeiras especializadas
- **Exame** - Economia, negócios e mercados
- **Estadão Economia** - Cobertura econômica abrangente
- **Money Times** - Mercado financeiro e investimentos
- **Bom Dia Mercado** - Morning Call e análises premium
- **Neo Feed** - Notícias de negócios e economia
- **Petro Notícias** - Setor energético e petróleo

## 🚀 Instalação Local

### Linux/Mac:
```bash
./install_local.sh
```

### Windows:
```batch
install_local.bat
```

## ⚙️ Configuração

1. Configure o arquivo `.env`:
```env
DATABASE_URL=postgresql://usuario:senha@host:5432/database
TRADERS_CLUB_USERNAME=seu_email@gmail.com
TRADERS_CLUB_PASSWORD=sua_senha
```

## 📝 Como Usar

### Executar uma vez:
```bash
python run_scraper.py --portal all
```

### Rodar 24/7 (automatizado):
```bash
python automated_scraper.py
```

### Portais específicos:
```bash
python run_scraper.py --portal bdm
python run_scraper.py --portal neofeed
python run_scraper.py --portal valor
```

## 🗃️ Estrutura do Banco

```sql
CREATE TABLE artigos_mercado (
    id SERIAL PRIMARY KEY,
    titulo TEXT NOT NULL,
    link_url TEXT UNIQUE NOT NULL,
    portal TEXT NOT NULL,
    resumo TEXT,
    conteudo_completo TEXT,
    autor TEXT,
    data_publicacao TIMESTAMP,
    categoria TEXT,
    tickers_relacionados JSONB DEFAULT '[]',
    data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔄 Sistema Automatizado

O `automated_scraper.py` executa:
- **Scraping**: A cada 2 horas
- **Health Check**: A cada 30 minutos
- **Logs**: Arquivo `automated_scraper.log`
- **Monitoramento**: Alertas automáticos em caso de falhas

## 📈 Recursos

- Coleta dados completos: título, conteúdo, autor, categoria
- Extração automática de tickers de ações brasileiras (XXXX3/4/11)
- Sistema robusto com tratamento de erros
- Logs detalhados para monitoramento
- Operação 24/7 com health checks

## 🛠️ Arquivos Principais

- `smart_scraper_expanded.py` - Engine principal de scraping
- `automated_scraper.py` - Sistema automatizado 24/7
- `run_scraper.py` - Interface de linha de comando
- `.env.example` - Exemplo de configuração

## 📊 Status Atual

- **171+ artigos** coletados
- **9 portais ativos** funcionando
- **Coleta automática** configurada
- **Dados completos** para análise