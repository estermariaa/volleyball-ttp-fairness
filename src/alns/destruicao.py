"""
Operadores de Destruição do ALNS.

O que este módulo faz:
Define as funções responsáveis por "desmontar" parcialmente uma tabela válida
sem quebrar a estrutura de pontos corridos.
Cada operador devolve: (tipo_de_reparo, matriz_do_1o_turno, itens_a_reparar).
"""

import random
import numpy as np


def espelhar(turno: np.ndarray) -> np.ndarray:
    """
    Como o campeonato é espelhado, só mexemos nas 11 rodadas do 1º turno
    e geramos o 2º turno invertendo o sinal (quem jogou em casa agora joga fora).
    """
    return np.vstack([turno, -turno])


def _aplicar_partial_swap_rounds(turno: np.ndarray, r1: int, r2: int, t_inicio: int) -> set:
    """
    Troca uma cadeia fechada (ciclo) de jogos entre as rodadas r1 e r2.
    Não dá para trocar só 1 jogo isolado entre duas rodadas porque os times
    ficariam repetidos na mesma rodada; seguindo o ciclo, a tabela continua válida.
    """
    ciclo = set()
    atual = t_inicio

    # Vou pulando de adversário em adversário entre r1 e r2 até fechar o ciclo
    while atual not in ciclo:
        ciclo.add(atual)
        adv_r1 = abs(turno[r1, atual]) - 1
        ciclo.add(adv_r1)
        atual = abs(turno[r2, adv_r1]) - 1

    # Agora sim posso trocar os jogos desses times entre r1 e r2
    for t in ciclo:
        turno[r1, t], turno[r2, t] = turno[r2, t], turno[r1, t]

    return ciclo


def destruir_rodadas(tabela: np.ndarray, k: int = 3):
    """
    Sorteia k rodadas do 1º turno para serem removidas e reinseridas
    em posições melhores na fase de reparo
    """
    n = tabela.shape[1]
    turno = tabela[: n - 1].copy()

    # Escolho k índices de rodadas (entre 0 e 10) sem repetição
    rodadas = random.sample(range(n - 1), k)
    return "rodadas", turno, rodadas


def destruir_times(tabela: np.ndarray, k: int = 3):
    """
    Sorteia k times para terem seus calendários completos permutados entre si.
    Ajuda muito na distância, porque aproxima times de regiões parecidas
    das sequências de viagem mais curtas.
    """
    n = tabela.shape[1]
    turno = tabela[: n - 1].copy()

    times = random.sample(range(n), k)
    return "times", turno, times


def destruir_mandos(tabela: np.ndarray, k: int = 8):
    """
    Sorteia k partidas distintas do 1º turno para o reparo decidir de novo
    quem joga em casa (+) e quem joga fora (-).
    """
    n = tabela.shape[1]
    turno = tabela[: n - 1].copy()
    jogos = set()

    # Uso set com (rodada, menor_id, maior_id) para não sortear o mesmo jogo duas vezes
    while len(jogos) < k:
        r = random.randrange(n - 1)
        t1 = random.randrange(n)
        t2 = abs(turno[r, t1]) - 1
        jogos.add((r, min(t1, t2), max(t1, t2)))

    return "mandos", turno, list(jogos)


def destruir_carryover(tabela: np.ndarray, k: int = 2):
    """
    Aplica k trocas parciais de rodadas para quebrar o padrão repetitivo
    de confrontos (carryover) e marca os jogos mexidos para ajustar os mandos.
    """
    n = tabela.shape[1]
    turno = tabela[: n - 1].copy()
    jogos_afetados = set()

    for _ in range(k):
        r1, r2 = random.sample(range(n - 1), 2)
        t_inicio = random.randrange(n)
        ciclo = _aplicar_partial_swap_rounds(turno, r1, r2, t_inicio)

        # Guardo os jogos que mudaram de lugar para o reparo arrumar os mandos depois
        for r in (r1, r2):
            for t1 in ciclo:
                t2 = abs(turno[r, t1]) - 1
                jogos_afetados.add((r, min(t1, t2), max(t1, t2)))

    jogos_lista = list(jogos_afetados)
    random.shuffle(jogos_lista)

    # Limito a 8 jogos para o reparo não ficar pesado demais em uma única iteração
    return "mandos", turno, jogos_lista[:8]


OPERADORES_DESTRUICAO = [
    ("destruir_rodadas", destruir_rodadas),
    ("destruir_times", destruir_times),
    ("destruir_mandos", destruir_mandos),
    ("destruir_carryover", destruir_carryover),
]