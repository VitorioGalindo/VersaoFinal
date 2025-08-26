import os
import sys
import subprocess
import time

def check_portfolio_logs():
    # Verificar se há logs do backend
    log_file = "logs/backend.log"
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # Mostrar as últimas 100 linhas do log
            for line in lines[-100:]:
                if "portfolio" in line.lower() or "cota" in line.lower() or "valor" in line.lower():
                    print(line.strip())
    else:
        print(f"Arquivo de log {log_file} não encontrado")

if __name__ == "__main__":
    check_portfolio_logs()