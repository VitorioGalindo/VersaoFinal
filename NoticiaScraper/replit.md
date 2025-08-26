# Overview

This is a Brazilian financial news scraper system designed to automatically collect and analyze news articles from major financial news portals including InfoMoney, G1, Brazil Journal, and Valor Econômico. The system extracts Brazilian stock tickers (XXXX3, XXXX4, XXXX11 format) from articles and stores the collected data in a PostgreSQL database for further analysis.

**Status Update (August 2025)**: System massively expanded to 13 Brazilian financial news portals with enhanced data collection:
- ✅ Working Perfectly: G1, Brazil Journal, Valor Econômico, Exame, Estadão, Money Times, Bom Dia Mercado, Neo Feed, Petro Notícias (9 portals)
- ⚠️ Partial: InfoMoney (requires JavaScript), UOL Economia (access restricted), CNN Brasil (needs selector adjustment), Traders Club (requires login credentials)
- Total articles collected: 110+ from active portals
- Enhanced data extraction: Now populates all database fields including author, publication date, full content, stock tickers, and categories

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Components

**Web Scraping Engine**: The system uses a hybrid approach combining traditional HTTP requests with BeautifulSoup and advanced Selenium WebDriver for JavaScript-heavy sites. Due to environment limitations, the system primarily uses requests + BeautifulSoup + trafilatura for reliable content extraction. Selenium is available as a fallback but requires Chromium browser setup.

**Content Processing Pipeline**: Articles are processed through multiple stages:
- Raw HTML extraction using requests/Selenium
- Content parsing with BeautifulSoup and trafilatura for clean text extraction
- Brazilian stock ticker extraction using regex patterns (XXXX3/4/11 format)
- Metadata extraction including publication dates, categories, and URLs

**Data Storage**: PostgreSQL database stores structured article data including content, metadata, extracted tickers, and timestamps. The system uses psycopg2 for database connectivity.

**Multi-Portal Support**: Modular scraper design supports 13 Brazilian financial news portals with portal-specific parsing logic:
- G1 financial sections (working)
- Brazil Journal (working)
- Valor Econômico (working)
- Exame (working - economy, business, markets sections)
- Estadão Economia (working)
- Money Times (working - comprehensive financial coverage)
- Bom Dia Mercado (working - includes Morning Call and BDM Express premium content)
- Neo Feed (working - principal, negócios, economia sections)
- Petro Notícias (working - energy and petroleum focus)
- InfoMoney (partial - requires JavaScript rendering)
- UOL Economia (partial - access restrictions)
- CNN Brasil Business (partial - needs selector updates)
- Traders Club Mover (partial - requires login credentials)

**Command Line Interface**: The run_scraper.py script provides flexible execution options allowing users to scrape all portals or target specific sites and categories.

**Automated Operation**: The automated_scraper.py provides 24/7 continuous operation with scheduled scraping every 2 hours, health checks every 30 minutes, and comprehensive logging for monitoring.

## Design Patterns

**Modular Architecture**: Each news portal has dedicated scraping functions while sharing common utilities for content extraction and database operations.

**Error Handling and Logging**: Comprehensive logging system tracks scraping operations, errors, and performance metrics with both file and console output.

**Rate Limiting**: Built-in delays and respectful scraping practices to avoid overwhelming target websites.

# External Dependencies

**Database**: PostgreSQL for persistent storage of scraped articles and metadata

**Web Scraping Libraries**:
- Selenium WebDriver with Chrome driver for JavaScript-heavy sites
- BeautifulSoup4 for HTML parsing
- trafilatura for content extraction
- selenium-stealth for bot detection avoidance

**HTTP Libraries**: requests for standard web requests

**Environment Management**: python-dotenv for configuration management

**Brazilian Timezone Support**: pytz for proper timestamp handling in Brazilian timezone

**Package Management**: webdriver-manager for automatic Chrome driver management

The system requires Chrome browser installation and appropriate database credentials configured through environment variables.