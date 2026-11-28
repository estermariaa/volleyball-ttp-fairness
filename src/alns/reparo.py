"""
Operadores de Reparo do ALNS.

O que este módulo faz:
Recebe a estrutura parcialmente destruída e a reconstrói testando alternativas
e avaliando cada uma pela função objetivo normalizada.
Suporta duas estratégias:
- 'guloso': escolhe sempre a melhor opção exata.
- 'ruido': sorteia entre as 2 melhores opções (ajuda a fugir de ótimos locais).
"""

import itertools
import random
import numpy as np
from .destruicao import espelhar


def _escolher_candidato(candidatos: list, modo: str) -> np.ndarray:
    """
    Recebe uma lista de (custo, turno_candidato), ordena do menor custo
    para o maior e devolve o escolhido conforme o modo ('guloso' ou 'ruido').
    """
    candidatos.sort(key=lambda x: x[0])

    # No modo 'ruido', dou uma pequena chance de pegar o 2º melhor para diversificar
    if modo == "ruido" and len(candidatos) >= 2:
        return random.choice(candidatos[:2])[1]

    return candidatos[0][1]


def _permutar_times(turno: np.ndarray, times_orig: list, perm: tuple) -> np.ndarray:
    """
    Troca o calendário completo entre os times selecionados seguindo a permutação 'perm'.
    Preciso trocar tanto as colunas quanto os números dentro da matriz (mantendo + e -).
    """
    novo = turno.copy()

    # Lembra que os IDs dentro da matriz vão de 1 a 12 (índice + 1)
    mapa_ids = {t_orig + 1: t_novo + 1 for t_orig, t_novo in zip(times_orig, perm)}

    # 1º passo: copio a coluna inteira de cada time para a sua nova posição
    for t_orig, t_novo in zip(times_orig, perm):
        novo[:, t_novo] = turno[:, t_orig]

    # 2º passo: atualizo as referências de quem enfrenta quem sem perder o sinal de mando
    copia_vals = novo.copy()
    for id_antigo, id_novo in mapa_ids.items():
        mask = np.abs(copia_vals) == id_antigo
        novo[mask] = np.sign(copia_vals[mask]) * id_novo

    return novo


def reparar_solucao(
    tipo: str,
    turno: np.ndarray,
    itens: list,
    inst,
    calcular_fo,
    pesos_fo: tuple[float, float, float],
    modo: str,
) -> np.ndarray:
    """
    Reconstrói a parte destruída da tabela de acordo com o tipo de destruição
    e devolve a tabela completa (22x12) já espelhada.
    """
    n = inst.n
    atual = turno.copy()

    if tipo == "rodadas":
        # Para cada rodada sorteada, tiro ela do lugar e testo reinserir em todas as 11 posições
        for r_idx in itens:
            rodada = atual[r_idx].copy()
            base = np.delete(atual, r_idx, axis=0)
            candidatos = []

            for pos in range(n - 1):
                cand = np.insert(base, pos, rodada, axis=0)
                custo, _ = calcular_fo(espelhar(cand), inst, pesos=pesos_fo)
                candidatos.append((custo, cand))

            atual = _escolher_candidato(candidatos, modo)

    elif tipo == "times":
        # Com k=3 times, são só 3! = 6 permutações possíveis, então testo todas
        candidatos = []
        for perm in itertools.permutations(itens):
            cand = _permutar_times(atual, itens, perm)
            custo, _ = calcular_fo(espelhar(cand), inst, pesos=pesos_fo)
            candidatos.append((custo, cand))

        atual = _escolher_candidato(candidatos, modo)

    elif tipo == "mandos":
        # Para cada jogo marcado, testo manter o mando atual vs inverter o mando
        for r, t1, t2 in itens:
            cand_orig = atual.copy()
            custo_orig, _ = calcular_fo(espelhar(cand_orig), inst, pesos=pesos_fo)

            cand_inv = atual.copy()
            cand_inv[r, t1] = -cand_inv[r, t1]
            cand_inv[r, t2] = -cand_inv[r, t2]
            custo_inv, _ = calcular_fo(espelhar(cand_inv), inst, pesos=pesos_fo)

            atual = _escolher_candidato(
                [(custo_orig, cand_orig), (custo_inv, cand_inv)], modo
            )

    return espelhar(atual)


OPERADORES_REPARO = ["guloso", "ruido"]