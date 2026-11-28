"""
Solver do ALNS.

O que este módulo faz:
Orquestra o loop principal do ALNS seguindo o pseudocódigo de Ropke & Pisinger (2006):
1. Parte da solução inicial viável (Método do Polígono).
2. A cada iteração, pede ao GerenciadorAdaptativo um par (destruição, reparo).
3. Gera a solução vizinha s' e aplica o critério de aceitação de Metropolis (SA).
4. Atualiza a melhor solução global (s_best) e recalcula os pesos a cada segmento.
"""

import math
import random
import time
import numpy as np

from .adaptacao import GerenciadorAdaptativo
from .destruicao import OPERADORES_DESTRUICAO
from .reparo import OPERADORES_REPARO, reparar_solucao


def executar_alns(
    inst,
    solucao_inicial: np.ndarray,
    calcular_fo,
    pesos_fo: tuple[float, float, float] = (1 / 3, 1 / 3, 1 / 3),
    max_iter: int = 1200,
    segmento: int = 50,
    rho: float = 0.2,
    T_inicial: float = 0.05,
    alpha: float = 0.996,
    seed: int = 42,
):
    random.seed(seed)
    np.random.seed(seed)

    # Instancio o controlador da roleta adaptativa com os nomes dos operadores
    nomes_dest = [nome for nome, _ in OPERADORES_DESTRUICAO]
    adaptador = GerenciadorAdaptativo(nomes_dest, OPERADORES_REPARO, rho=rho)

    # Avalio a solução inicial (Polígono) para ter o ponto de partida
    s = solucao_inicial.copy()
    custo_atual, met_atual = calcular_fo(s, inst, pesos=pesos_fo)

    s_best = s.copy()
    melhor_custo = custo_atual
    melhores_metricas = met_atual

    T = T_inicial
    inicio = time.time()

    for it in range(1, max_iter + 1):
        # Roleta escolhe qual destruição e qual reparo vou usar agora
        idx_d, idx_r = adaptador.selecionar_operadores()
        _, fn_dest = OPERADORES_DESTRUICAO[idx_d]
        modo_rep = OPERADORES_REPARO[idx_r]

        # Destrói parte da tabela atual e reconstrói para gerar s'
        tipo, turno_base, itens = fn_dest(s)
        s_cand = reparar_solucao(tipo, turno_base, itens, inst, calcular_fo, pesos_fo, modo_rep)
        custo_cand, met_cand = calcular_fo(s_cand, inst, pesos=pesos_fo)

        # Critério de aceitação (Metropolis/Simulated Annealing) + pontuação
        if custo_cand < melhor_custo:
            # Novo recorde global
            s = s_cand
            custo_atual = custo_cand
            s_best = s_cand.copy()
            melhor_custo = custo_cand
            melhores_metricas = met_cand
            adaptador.registrar_resultado(idx_d, idx_r, "melhor_global")

        elif custo_cand < custo_atual:
            # Não bateu o recorde global, mas melhorou a tabela atual
            s = s_cand
            custo_atual = custo_cand
            adaptador.registrar_resultado(idx_d, idx_r, "melhor_atual")

        else:
            # Ficou pior: aceito com probabilidade exp(delta / T) para escapar de ótimo local
            delta = custo_atual - custo_cand  # fica negativo
            if random.random() < math.exp(delta / max(T, 1e-9)):
                s = s_cand
                custo_atual = custo_cand
                adaptador.registrar_resultado(idx_d, idx_r, "aceita_sa")

        # Resfrio a temperatura aos poucos
        T *= alpha

        # A cada 'segmento' iterações, atualizo os pesos da roleta
        if it % segmento == 0:
            adaptador.atualizar_pesos()

    tempo_total = time.time() - inicio
    return s_best, melhores_metricas, tempo_total, adaptador.resumo_pesos()