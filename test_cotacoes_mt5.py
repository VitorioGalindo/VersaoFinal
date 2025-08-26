#!/usr/bin/env python3
"""
Script para testar cotações MetaTrader5 - VERSÃO CORRIGIDA
Não depende de seleção de símbolos

Requer as variáveis de ambiente ``MT5_LOGIN``, ``MT5_PASSWORD`` e ``MT5_SERVER`` definidas.
"""

import os
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent / 'projeto-final'))

def test_mt5_quotes_fixed():
    """Testa cotações MetaTrader5 sem depender de seleção"""
    
    print("🧪 TESTE CORRIGIDO DE COTAÇÕES METATRADER5")
    print("=" * 60)
    
    try:
        import MetaTrader5 as mt5
        print("✅ MetaTrader5 importado com sucesso")
    except ImportError:
        print("❌ MetaTrader5 não disponível")
        return
    
    # Configurações
    try:
        MT5_LOGIN = int(os.environ["MT5_LOGIN"])
        MT5_PASSWORD = os.environ["MT5_PASSWORD"]
        MT5_SERVER = os.environ["MT5_SERVER"]
    except KeyError as e:
        raise EnvironmentError(
            f"Variável de ambiente {e.args[0]} não definida. "
            "Configure MT5_LOGIN, MT5_PASSWORD e MT5_SERVER antes de rodar o teste."
        ) from e

    print(f"🔐 Login: {MT5_LOGIN}")
    print(f"🌐 Servidor: {MT5_SERVER}")
    
    # Inicializar MT5
    print("\n🚀 Inicializando MetaTrader5...")
    if not mt5.initialize():
        print(f"❌ Falha ao inicializar: {mt5.last_error()}")
        return
    
    print("✅ MetaTrader5 inicializado")
    
    # Fazer login
    print(f"\n🔑 Fazendo login...")
    if not mt5.login(MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER):
        print(f"❌ Falha no login: {mt5.last_error()}")
        mt5.shutdown()
        return
    
    print("✅ Login realizado com sucesso")
    
    # Obter símbolos já selecionados no Market Watch
    print(f"\n📋 Obtendo símbolos do Market Watch...")
    selected_symbols = mt5.symbols_get(group="*")
    
    if selected_symbols:
        print(f"✅ Total de símbolos disponíveis: {len(selected_symbols)}")
        
        # Filtrar símbolos brasileiros principais
        main_tickers = ['PETR4', 'VALE3', 'ABEV3', 'ITUB4', 'BBDC4']
        available_symbols = []
        
        for symbol in selected_symbols:
            for ticker in main_tickers:
                if symbol.name == ticker:
                    available_symbols.append(symbol)
        
        print(f"📊 Símbolos principais encontrados: {[s.name for s in available_symbols]}")
        
        # Testar cotações dos símbolos disponíveis
        print(f"\n💹 TESTANDO COTAÇÕES (SEM SELEÇÃO):")
        print("-" * 50)
        
        test_symbols = available_symbols[:5] if available_symbols else []
        
        if not test_symbols:
            print("⚠️ Nenhum símbolo principal encontrado. Testando primeiros 3 símbolos...")
            test_symbols = selected_symbols[:3]
        
        for symbol in test_symbols:
            symbol_name = symbol.name
            print(f"\n🔍 Testando {symbol_name}:")
            print(f"  📝 Descrição: {symbol.description}")
            print(f"  📊 Já selecionado: {symbol.select}")
            
            # MÉTODO 1: Tentar obter tick diretamente
            print(f"  🔄 Método 1: symbol_info_tick...")
            tick = mt5.symbol_info_tick(symbol_name)
            if tick:
                print(f"  ✅ SUCESSO! Tick obtido:")
                print(f"    💰 Bid: {tick.bid}")
                print(f"    💰 Ask: {tick.ask}")
                print(f"    💰 Last: {tick.last}")
                print(f"    📊 Volume: {tick.volume}")
                print(f"    ⏰ Time: {tick.time}")
                continue
            else:
                print(f"  ❌ Tick não disponível")
            
            # MÉTODO 2: Tentar dados históricos M1
            print(f"  🔄 Método 2: Dados históricos M1...")
            rates = mt5.copy_rates_from_pos(symbol_name, mt5.TIMEFRAME_M1, 0, 1)
            if rates is not None and len(rates) > 0:
                rate = rates[0]
                print(f"  ✅ SUCESSO! Dados históricos M1:")
                print(f"    💰 Open: {rate['open']}")
                print(f"    💰 High: {rate['high']}")
                print(f"    💰 Low: {rate['low']}")
                print(f"    💰 Close: {rate['close']}")
                print(f"    📊 Volume: {rate['tick_volume']}")
                continue
            else:
                print(f"  ❌ Dados M1 não disponíveis")
            
            # MÉTODO 3: Tentar dados históricos D1
            print(f"  🔄 Método 3: Dados históricos D1...")
            rates = mt5.copy_rates_from_pos(symbol_name, mt5.TIMEFRAME_D1, 0, 1)
            if rates is not None and len(rates) > 0:
                rate = rates[0]
                print(f"  ✅ SUCESSO! Dados históricos D1:")
                print(f"    💰 Open: {rate['open']}")
                print(f"    💰 High: {rate['high']}")
                print(f"    💰 Low: {rate['low']}")
                print(f"    💰 Close: {rate['close']}")
                print(f"    📊 Volume: {rate['tick_volume']}")
                continue
            else:
                print(f"  ❌ Dados D1 não disponíveis")
            
            # MÉTODO 4: Informações básicas do símbolo
            print(f"  🔄 Método 4: Informações do símbolo...")
            symbol_info = mt5.symbol_info(symbol_name)
            if symbol_info:
                print(f"  ✅ Informações básicas:")
                print(f"    💰 Bid: {symbol_info.bid}")
                print(f"    💰 Ask: {symbol_info.ask}")
                print(f"    📊 Volume: {symbol_info.volume}")
                if hasattr(symbol_info, 'last'):
                    print(f"    💰 Last: {symbol_info.last}")
            else:
                print(f"  ❌ Informações do símbolo não disponíveis")
        
        # Testar forçar seleção de um símbolo específico
        print(f"\n🔧 TESTE ESPECIAL: Forçar seleção PETR4")
        print("-" * 40)
        
        # Primeiro verificar se PETR4 existe
        petr4_info = mt5.symbol_info("PETR4")
        if petr4_info:
            print(f"✅ PETR4 encontrado: {petr4_info.description}")
            print(f"📊 Selecionado: {petr4_info.select}")
            
            # Tentar diferentes métodos de seleção
            print(f"🔄 Tentando mt5.symbol_select('PETR4', True)...")
            result1 = mt5.symbol_select("PETR4", True)
            print(f"Resultado: {result1}")
            
            if not result1:
                print(f"🔄 Tentando adicionar ao Market Watch...")
                # Tentar adicionar explicitamente
                result2 = mt5.market_book_add("PETR4")
                print(f"Market book add: {result2}")
            
            # Verificar novamente
            petr4_info_after = mt5.symbol_info("PETR4")
            if petr4_info_after:
                print(f"📊 Selecionado após tentativa: {petr4_info_after.select}")
                
                # Tentar obter tick agora
                tick_after = mt5.symbol_info_tick("PETR4")
                if tick_after:
                    print(f"🎉 SUCESSO! Tick PETR4 obtido após seleção:")
                    print(f"  💰 Bid: {tick_after.bid}")
                    print(f"  💰 Ask: {tick_after.ask}")
                    print(f"  💰 Last: {tick_after.last}")
                else:
                    print(f"❌ Ainda não conseguiu obter tick")
        
    else:
        print("❌ Nenhum símbolo encontrado")
    
    # Finalizar
    print(f"\n🛑 Finalizando...")
    mt5.shutdown()
    print("✅ Teste concluído")

if __name__ == '__main__':
    test_mt5_quotes_fixed()
