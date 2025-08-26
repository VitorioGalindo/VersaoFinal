# Simulação do cálculo da cota
patrimonio_liquido_ajustado = 8774191.77
qtd_cotas = 86634.0000
cota_d1 = 113.8200

print(f"Valores para cálculo:")
print(f"  patrimonio_liquido_ajustado: {patrimonio_liquido_ajustado}")
print(f"  qtd_cotas: {qtd_cotas}")
print(f"  cota_d1: {cota_d1}")

# Cálculo do valor da cota
if qtd_cotas and qtd_cotas != 0:
    valor_cota = patrimonio_liquido_ajustado / qtd_cotas
    print(f"  valor_cota: {valor_cota}")
else:
    valor_cota = 0.0
    print("  qtd_cotas é zero ou None, definindo valor_cota como 0.0")

# Cálculo da variação da cota
if cota_d1 and cota_d1 != 0:
    variacao_cota_pct = ((valor_cota / cota_d1) - 1) * 100
    print(f"  variacao_cota_pct: {variacao_cota_pct}")
else:
    variacao_cota_pct = 0.0
    print("  cota_d1 é zero ou None, definindo variacao_cota_pct como 0.0")