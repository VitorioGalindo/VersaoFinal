#!/usr/bin/env python3
"""
WORKER RTD DESCONTINUADO

Este worker foi descontinuado e substituído pelo worker integrado no backend em:
`backend/services/metatrader5_rtd_worker.py`

Para executar o sistema com atualização em tempo real, utilize:
`python run_backend_mt5.py`

Este arquivo é mantido apenas para referência histórica.
"""

import sys
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.warning("=" * 60)
    logger.warning("WORKER RTD DESCONTINUADO")
    logger.warning("=" * 60)
    logger.warning("Este worker foi descontinuado e substituído.")
    logger.warning("")
    logger.warning("Para executar o sistema com atualização em tempo real:")
    logger.warning("  python run_backend_mt5.py")
    logger.warning("")
    logger.warning("Veja rtd-metatrader/README.md para mais informações.")
    logger.warning("=" * 60)
    
    # Sair com código de erro para indicar que não deve ser usado
    sys.exit(1)

if __name__ == "__main__":
    main()