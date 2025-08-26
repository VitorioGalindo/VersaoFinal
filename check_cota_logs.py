import os
import sys
import subprocess
import time

def check_cota_logs():
    # Verificar se há logs do backend
    log_file = "logs/backend.log"
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # Mostrar as linhas relacionadas ao cálculo da cota
            for line in lines:
                if "cota" in line.lower() or "valor_cota" in line.lower() or "variacao_cota" in line.lower():
                    print(line.strip())
    else:
        print(f"Arquivo de log {log_file} não encontrado")

if __name__ == "__main__":
    check_cota_logs()