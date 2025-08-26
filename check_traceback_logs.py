import os
import sys
import subprocess
import time

def check_traceback_logs():
    # Verificar se há logs do backend
    log_file = "logs/backend.log"
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            # Mostrar as linhas que contêm "traceback" ou "error"
            for line in lines:
                if "traceback" in line.lower() or "error" in line.lower():
                    print(line.strip())
    else:
        print(f"Arquivo de log {log_file} não encontrado")

if __name__ == "__main__":
    check_traceback_logs()