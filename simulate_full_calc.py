# Vamos criar um script para verificar se há algum problema com a ordem das operações
# Vamos simular o código exatamente como está no backend

# Valores simulados do banco de dados
editable_metrics = {
    "cotaD1": 113.8200,
    "qtdCotas": 86634.0000,
    "caixaBruto": 1371514.0000
}

# Valores simulados do cálculo das posições
total_value = 8774191.77
total_long = 10242178.08
total_short = -1467986.31

print("Valores iniciais:")
print(f"  editable_metrics: {editable_metrics}")
print(f"  total_value: {total_value}")
print(f"  total_long: {total_long}")
print(f"  total_short: {total_short}")

# Obter valores editáveis
cota_d1 = editable_metrics.get("cotaD1", 0.0)
qtd_cotas = editable_metrics.get("qtdCotas", 0.0)
caixa_bruto = editable_metrics.get("caixaBruto", 0.0)

print("\nValores obtidos das métricas editáveis:")
print(f"  cota_d1: {cota_d1}")
print(f"  qtd_cotas: {qtd_cotas}")
print(f"  caixa_bruto: {caixa_bruto}")

# Converter para float
try:
    cota_d1 = float(cota_d1) if cota_d1 is not None else 0.0
except (ValueError, TypeError):
    cota_d1 = 0.0

try:
    qtd_cotas = float(qtd_cotas) if qtd_cotas is not None else 0.0
except (ValueError, TypeError):
    qtd_cotas = 0.0

try:
    caixa_bruto = float(caixa_bruto) if caixa_bruto is not None else 0.0
except (ValueError, TypeError):
    caixa_bruto = 0.0

print("\nValores convertidos para float:")
print(f"  cota_d1: {cota_d1}")
print(f"  qtd_cotas: {qtd_cotas}")
print(f"  caixa_bruto: {caixa_bruto}")

# Calcular patrimônio líquido ajustado
patrimonio_liquido = total_value
try:
    patrimonio_liquido = float(patrimonio_liquido) if patrimonio_liquido is not None else 0.0
except (ValueError, TypeError):
    patrimonio_liquido = 0.0

patrimonio_liquido_ajustado = patrimonio_liquido
print(f"\nPatrimônio líquido ajustado: {patrimonio_liquido_ajustado}")

# Calcular valor da cota
print(f"\nValores antes do cálculo da cota - patrimonio_liquido_ajustado: {patrimonio_liquido_ajustado}, qtd_cotas: {qtd_cotas}")
if qtd_cotas and qtd_cotas != 0:
    try:
        resultado_divisao = patrimonio_liquido_ajustado / qtd_cotas
        print(f"Divisão: {patrimonio_liquido_ajustado} / {qtd_cotas} = {resultado_divisao}")
        valor_cota = resultado_divisao
    except (ZeroDivisionError, ValueError, TypeError) as e:
        print(f"Erro na divisão para cálculo da cota: {e}")
        valor_cota = 0.0
else:
    print("qtd_cotas é zero ou None, definindo valor_cota como 0.0")
    valor_cota = 0.0
print(f"Valor da cota calculado: {valor_cota}")

# Calcular variação da cota
print(f"\nValores para cálculo da variação da cota - valor_cota: {valor_cota}, cota_d1: {cota_d1}")
if cota_d1 and cota_d1 != 0:
    try:
        variacao = ((valor_cota / cota_d1) - 1) * 100
        print(f"Variação da cota: (({valor_cota} / {cota_d1}) - 1) * 100 = {variacao}")
        variacao_cota_pct = variacao
    except (ZeroDivisionError, ValueError, TypeError) as e:
        print(f"Erro no cálculo da variação da cota: {e}")
        variacao_cota_pct = 0.0
else:
    print("cota_d1 é zero ou None, definindo variacao_cota_pct como 0.0")
    variacao_cota_pct = 0.0
print(f"Variação da cota calculada: {variacao_cota_pct}")