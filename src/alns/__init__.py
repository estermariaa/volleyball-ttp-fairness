"""
Este arquivo apenas expõe a função principal 'executar_alns' para
que outros scripts possam importar direto com: from alns import executar_alns
"""

from .solver import executar_alns

__all__ = ["executar_alns"]