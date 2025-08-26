# 🚀 Como Executar Localmente

## 📁 Arquivos Principais para Download

Baixe estes arquivos essenciais:

### Código Principal:
- `smart_scraper_expanded.py` - Engine de scraping
- `automated_scraper.py` - Sistema 24/7
- `run_scraper.py` - Interface linha de comando
- `.env.example` - Configurações de exemplo

### Scripts de Instalação:
- `install_local.sh` (Linux/Mac)
- `install_local.bat` (Windows)

### Documentação:
- `README.md` - Guia completo
- `replit.md` - Arquitetura técnica

## 🛠️ Instalação Rápida

### Linux/Mac:
```bash
# 1. Baixar arquivos
# 2. Dar permissão
chmod +x install_local.sh

# 3. Executar instalação
./install_local.sh

# 4. Configurar .env
cp .env.example .env
# Editar .env com suas configurações
```

### Windows:
```batch
# 1. Baixar arquivos
# 2. Executar instalação
install_local.bat

# 3. Configurar .env
copy .env.example .env
# Editar .env com suas configurações
```

## ⚙️ Configuração do .env

```env
# Banco PostgreSQL (obrigatório)
DATABASE_URL=postgresql://usuario:senha@host:5432/database

# Traders Club (opcional)
TRADERS_CLUB_USERNAME=seu_email@gmail.com
TRADERS_CLUB_PASSWORD=sua_senha
```

## 🎯 Como Executar

### Opção 1: Uma vez só
```bash
python run_scraper.py --portal all
```

### Opção 2: Sistema 24/7 (recomendado)
```bash
python automated_scraper.py
```

Este comando vai:
- Coletar notícias a cada 2 horas
- Fazer health check a cada 30 minutos  
- Salvar logs em `automated_scraper.log`
- Rodar continuamente até você parar (Ctrl+C)

### Opção 3: Portais específicos
```bash
python run_scraper.py --portal bdm        # Só Bom Dia Mercado
python run_scraper.py --portal neofeed    # Só Neo Feed
python run_scraper.py --portal valor      # Só Valor Econômico
```

## 📊 Monitoramento

- **Logs**: `automated_scraper.log`
- **Banco**: Conecte no PostgreSQL e consulte tabela `artigos_mercado`
- **Status**: O script mostra estatísticas a cada ciclo

## 🎉 Pronto!

Sistema configurado para coletar notícias de 9 portais brasileiros automaticamente!